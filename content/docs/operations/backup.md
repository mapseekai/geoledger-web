---
title: "备份、导出与恢复"
linkTitle: "备份与恢复"
description: "选择数据库恢复或逻辑迁移，并在隔离目标核对版本与发布链路。"
weight: 30
lastmod: 2026-10-29
---

故障恢复依赖独立备份。业务修订用于追溯要素变化，不能代替数据库与持久化介质的恢复副本。

## 前置条件与工具选择

固定服务端版本，准备可读取的源库、新输出路径和隔离恢复目标。先核对[存储兼容性]({{< relref "/docs/reference/compatibility/" >}})，再选择工具。

| 方式 | 用途 | 恢复边界 |
|---|---|---|
| SQLite backup / restore | 同后端完整恢复 | 身份、原生空间元数据与索引 |
| PostgreSQL 原生备份 | 原表和版本系统共同恢复 | 业务表、GeoLedger 表、触发器与数据库所需角色 |
| 逻辑 export / import | 业务数据导出与跨后端迁移 | 版本业务数据，不原样重建身份凭据与外部表绑定 |

以下 SQLite 命令从已构建的 GeoLedger 仓库根目录执行。读取和导出不修改源数据；恢复与导入只对全新隔离目标执行。输出文件使用尚不存在的新路径。

## 1. 创建备份与逻辑导出

```sh
./target/release/geoledger-server --storage sqlite --data-dir ./geoledger-data \
  backup --output ./geoledger-backup.sqlite3

./target/release/geoledger-server --storage sqlite --data-dir ./geoledger-data \
  export --output ./geoledger-export.jsonl
```

backup 创建在线一致的 SQLite 备份并校验。export 在一致快照中输出 JSON 行、表级摘要和完整性校验和，服务可以继续运行。

## 2. 检查导出文件

```sh
./target/release/geoledger-server \
  verify --input ./geoledger-export.jsonl --file-only
```

成功表示文件结构、摘要与校验和符合逻辑格式。它不证明另一个运行库与该文件完全一致；去掉 file-only 时，Verify 还比较配置的数据库，差异退出码为 4。

## 3. 恢复到新目录

确认目标没有运行中的服务，也没有已有数据库。在新的临时目录恢复：

```sh
recovery_dir="$(mktemp -d)"
./target/release/geoledger-server --storage sqlite --data-dir "$recovery_dir" \
  restore --input ./geoledger-backup.sqlite3
```

Restore 校验后安装 SQLite 数据库，目标库已存在时拒绝替换。启动恢复实例前，为其分配与原服务不同的监听端口，并核对恢复后的身份凭据。

逻辑导入使用 `import --input <export-file>`，目标必须新建或为空；输入损坏时应保持数据库不变。该路径用于迁移，不能当成覆盖现有数据库的工具。

## 4. 验证恢复结果

在隔离实例检查 `/ready`、项目 HEAD、当前要素、旧修订、草稿、字段历史、审计与最近回执。再创建测试工作区，保存、发布并重放原请求。

只有备份与导出对应同一恢复点时，才将逐表 Verify 作为状态一致的比较证据。记录实际恢复版本、数据规模、结果和失败步骤；恢复时间由目标环境实测。

## PostGIS 与外部表

原生备份由 DBA 使用 pg_dump、数据库备份系统或基线备份配合 WAL 归档管理。恢复必须同时包含原表、版本表、绑定身份和保护触发器，仅恢复同名表不足以恢复纳管关系。

逻辑导入将纳管数据恢复为内部数据集，不自动重建外部表绑定。PostGIS 使用 export / import / verify；服务端 backup / restore 命令只处理 SQLite。

## 失败处理与回退

校验失败时保留源库、备份和错误记录，重新创建干净目标排查。恢复完成前不切换客户端，也不覆盖当前可用库；切换失败时回到原服务与原库。

恢复旧备份后核对用户和 Key 状态，必要时轮换再开放。执行项目或数据集删除前完成所需备份，删除会清理在线版本数据。

## 实现依据

- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/main.rs)
- [crates/engine/src/session/portable.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/session/portable.rs)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
- [scripts/backup-drill.sh](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/scripts/backup-drill.sh)
