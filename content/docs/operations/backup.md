---
title: "备份、可移植导出与灾难恢复"
linkTitle: "备份与恢复"
description: "制定 SQLite 与 PostGIS 的在线备份策略，使用可移植 JSONL 逻辑导出进行跨后端迁移与完整性校验，并在隔离环境完成恢复演练。"
weight: 30
lastmod: 2026-11-01
---

GeoLedger 的版本历史（Revision）用于业务层面的数据追溯与变更回退，而应对磁盘故障、主机损毁或误删项目的底线保障则依赖于**定期的独立数据库备份**。

`geoledger-server` 提供 `backup`、`restore`、`export`、`import` 和 `verify` 数据运维子命令。`backup` 与 `export` 可在源服务运行时创建一致性副本；`restore` 与 `import` 应在未运行服务的空目标中执行。

## 三种备份与迁移方式对比

在制定备份方案前，请先根据存储后端与恢复目标选择合适的工具：

| 备份 / 迁移方式 | 适用存储后端 | 包含的数据范围与恢复边界 |
|---|---|---|
| **1. SQLite 在线备份与离线恢复（`backup` / `restore`）** | 仅 SQLite + SpatiaLite | **全量物理级恢复**：通过 `VACUUM INTO` 创建在线一致性副本并校验，完整包含所有项目、自建数据表、原生空间索引、用户身份、密码哈希、API Key 摘要与审计日志 |
| **2. PostgreSQL 原生备份（`pg_dump` / PITR）** | 仅 PostgreSQL + PostGIS | **全库与纳管表协同恢复**：使用 `pg_dump -Fc` 或 `pg_basebackup` + WAL 归档，同时覆盖 GeoLedger 系统表（`gl_*`）、自建数据表、**外部纳管业务原表**以及保护触发器 |
| **3. 可移植逻辑导出（`export` / `import` / `verify`）** | SQLite 与 PostGIS 通用（支持跨后端互导） | **业务版本数据迁移**：在一致读快照中将项目、成员 UUID、数据集、工作区草稿、字段历史、修订、旧正文、发布回执与审计输出为带校验和的 JSONL 文件；**不包含用户密码与 API Key 摘要**，且导入时会将曾纳管的外部表恢复为内部自建数据集 |

> **安全与路径原则**：备份与导出包含业务数据及发布请求原文，应按生产机密等级加密保管。指定文件路径时，`backup` / `export` 以私有权限（`0600`）新建文件且不会覆盖已有文件；`export --output -` 也可写入标准输出，重定向文件的权限由 shell 和操作方负责。`restore` / `import` 仅允许写入未运行服务的全新空数据目录或空数据库。

## 步骤 1：创建在线备份与逻辑导出

当服务正在运行时，无需停机即可创建一致性快照（以下命令以本地编译的 Release 二进制为例；若使用统一容器，可通过 `docker compose exec geoledger geoledger-server ...` 执行）：

```sh
# 1. 创建 SQLite 在线物理备份（完成后自动验证数据库完整性与存储格式 19）
./target/release/geoledger-server --storage sqlite --data-dir ./geoledger-data \
  backup --output ./geoledger-backup.sqlite3

# 2. 创建与后端无关的 JSONL 逻辑导出（适用于 SQLite 或 PostGIS）
./target/release/geoledger-server --storage sqlite --data-dir ./geoledger-data \
  export --output ./geoledger-export.jsonl
```

- `backup` 命令会在备份完成后输出各表的精确行数与内容摘要。
- `export` 命令在单个只读事务快照中读取数据，并在 JSONL 文件末尾写入表级行数统计与 SHA-256 完整性校验和。

## 步骤 2：校验导出文件与数据库一致性（`verify`）

生成逻辑导出文件后，可使用 `verify` 命令随时检查文件是否完整无损：

```sh
# 仅校验导出文件本身的结构、表摘要与 SHA-256 校验和（无需连接数据库）
./target/release/geoledger-server \
  verify --input ./geoledger-export.jsonl --file-only
```

如果你在停机维护窗口内同时执行了导出与备份，希望验证某个目标数据库的内容与该导出文件**逐表逐行完全一致**，可去掉 `--file-only` 参数并指定目标库配置（若存在任何差异，命令将以退出码 `4` 报错退出）。

## 步骤 3：在隔离环境中执行恢复或导入

在切流或替换故障实例前，**请务必先在全新的隔离目录或空数据库中执行恢复**。停止使用目标目录或目标数据库的服务，切勿直接覆盖正在运行的源目录；创建备份时源服务可以继续运行：

```sh
# 创建全新的临时恢复目录，并将 SQLite 备份安装到该目录
recovery_dir="$(mktemp -d)"
./target/release/geoledger-server --storage sqlite --data-dir "$recovery_dir" \
  restore --input ./geoledger-backup.sqlite3
```

如果是跨后端迁移（例如将 SQLite 数据迁移至全新的空 PostGIS 数据库，或反之），则使用 `import` 命令：

```sh
# 将逻辑导出文件原子导入到全新的目标存储中
./target/release/geoledger-server --storage postgis \
  --database-url "$GL_DRILL_DATABASE_URL" \
  import --input ./geoledger-export.jsonl
```

`import` 会在单个事务内校验全部 JSON 行、表摘要与校验和，并自动重建每张数据集的独立物理表、原生几何列与空间索引；若输入文件存在任何截断或校验失败，整个导入事务将完整回滚，保持目标库干净。

## 步骤 4：恢复后的端到端验证清单

启动恢复后的新服务实例（测试时请绑定与线上不同的监听端口），按以下清单逐项核对后再切换客户端流量：

1. **探针与基础元数据**：请求 `GET /ready` 返回 `{"ok":true}`，调用 `info` 确认 `format_version` 为 `19`。
2. **版本与数据完整性**：核对各项目的 `HEAD` 修订号、当前要素、历史固定修订读取、开放工作区草稿、版本化字段历史（`schema`）、项目审计条数以及最近的发布回执（可通过重放最近一次 `publish` 的 `request_id` 验证幂等回执完好）。
3. **写入链路验证**：在测试项目上新建一个工作区，完成一次要素保存与发布，确认写事务与空间索引工作正常。
4. **身份与密钥安全复核**：
   - 若使用物理备份（`restore` 或 `pg_dump`）恢复了较早时间点的状态，请检查用户列表与 API Key，**立即撤销在备份时间点之后本已被吊销的旧密钥或离职人员账号**。
   - 若使用逻辑导入（`import`）迁移到新库，由于逻辑导出不包含用户密码与 API Key，请由管理员在新库中创建用户并重新绑定项目成员权限。

## PostGIS 纳管表的备份特别说明

如果你的 PostGIS 实例纳管了外部业务表（见 **[PostGIS 表纳管]({{< relref "/docs/guides/postgis/" >}})**），请特别注意：

- **必须同库整备**：使用 `pg_dump -Fc` 或物理备份时，必须将**外部业务源表**、**`gl_*` 系统表**以及**源表上的保护触发器**纳入同一次备份与恢复。如果只恢复了同名业务表而漏掉了版本表（或反之），服务启动及读写时的绑定身份与防漂移校验会拒绝操作。
- **参考自动化演练脚本**：仓库中的 `scripts/backup-drill.sh` 展示了完整的“写入 → 在线备份与导出 → 异地恢复 → `verify` 比对 → 跨库导入”自动化演练流程，建议生产环境每季度在隔离主机上使用真实备份执行一次恢复演练并记录实测 RTO。

## 实现依据

- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/main.rs)
- [crates/engine/src/session/portable.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/session/portable.rs)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
- [scripts/backup-drill.sh](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/scripts/backup-drill.sh)
