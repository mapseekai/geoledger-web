---
title: "纳管已有 PostGIS 业务表"
linkTitle: "PostGIS 表纳管"
description: "在不搬迁存量数据的前提下，将 PostgreSQL/PostGIS 中的既有业务表注册为 GeoLedger 数据集，实现工作区编辑、事务写回与历史追溯。"
weight: 30
lastmod: 2026-10-29
---

在许多生产系统中，企业已经拥有正在运行的 PostgreSQL + PostGIS 空间业务表（如道路网、地块边界、管网设施），并有报表或下游服务直接读取这些表。

GeoLedger 的 **PostGIS 表纳管（Table Registration）** 能力允许你在不复制存量几何与属性数据的前提下，将符合契约的现有业务表直接绑定为 GeoLedger 数据集：
- **零数据冗余初始化**：注册时仅建立表绑定元数据、保护触发器、必要的窄 ID 排序索引与初始提交记录，原有的业务行继续留在源表中。
- **工作区隔离与事务写回**：未发布的草稿保存在 GeoLedger 版本表中；正式发布时，GeoLedger 在**同一个数据库事务**内将增删改写回原业务表，同时把被替换或删除的旧正文归档到历史表。

## 前置条件与源表契约检查

在生产库执行纳管前，请先在隔离的数据库副本上验证以下要求：

| 检查维度 | 契约要求与说明 |
|---|---|
| **操作者身份** | 调用方必须同时具备 **平台管理员（`platform_admin`）** 身份以及目标项目的 **可写成员（`owner` 或 `editor`）** 权限 |
| **主键列（`id_column`）** | 必须为**单列主键**，支持整数、文本（`text` / `varchar`，UTF-8 编码不超过 256 字节且不含控制字符）或 `uuid` 类型（支持普通主键或可延迟主键） |
| **几何列（`geometry_column`）** | 必须为声明了具体几何子类型（`Point`、`LineString`、`Polygon` 或对应的 `Multi*`）与坐标维度（XY / XYZ）的 PostGIS `geometry` 列；若列声明 SRID 为 `0`，则全表各行几何的 SRID 必须一致 |
| **属性列** | 其余普通可写列自动映射为要素属性（最多 256 列），支持通过[版本化字段定义]({{< relref "/docs/guides/schema/" >}})新增或删除普通可空列 |
| **数据库账号权限** | GeoLedger 运行账号需具备对该业务表的 `SELECT`、`INSERT`、`UPDATE`、`DELETE` 以及**表所有权（或等效的父角色权限）**，以便在纳管和发布时执行锁表、维护保护触发器与必要的索引（仅授予 `TRIGGER` 权限不足以覆盖完整生命周期） |

> **性能与锁等待提示**：注册纳管表时，GeoLedger 会以有界分页只读扫描源表，校验每行几何的有限数值与 GeoJSON 结构兼容性，并在缺少兼容主键排序索引时创建窄 ID 索引。因此，大表首次注册的耗时取决于源表数据规模、现有索引与锁等待情况，建议在业务低峰期执行。

## 步骤 1：配置 PostGIS 存储后端

首先由 DBA 在目标 PostgreSQL 数据库中启用 PostGIS 扩展（`CREATE EXTENSION IF NOT EXISTS postgis;`），并配置受限的服务运行角色。

按 **[部署与运行指南]({{< relref "/docs/operations/deployment/" >}})** 启动 `geoledger-server`，显式指定 `postgis` 存储引擎与加密数据库连接串：

```sh
export GL_STORAGE=postgis
export GL_DATABASE_URL='postgresql://geoledger_app@db.internal:5432/geoledger?sslmode=verify-full&sslrootcert=/etc/geoledger/db-ca.pem'
```

启动后调用 `curl --fail http://127.0.0.1:7881/ready` 确认数据库连接与版本表初始化成功。

## 步骤 2：将业务表注册为数据集

你可以通过 **Web 控制台**、**四语言 SDK** 或 **HTTP API / CLI** 执行表注册：

- **Web 控制台**：进入目标项目的 **数据集** 页面，点击 **创建数据集**，在数据来源中选择 **纳管已有 PostGIS 表**，填入 `schema`、表名、主键列名和几何列名。
- **四语言 SDK**：调用专门的注册方法，系统会自动从源表几何列读取几何类型、坐标维度与 SRID：
  - Python：`client.register_table(project.id, "roads", schema="public", table="roads", id_column="id", geometry_column="geom")`
  - Rust：`client.register_table(&project.id, "roads", &PostgisTable { ... }).await?`
  - Go：`client.RegisterTable(ctx, project.ID, "roads", geoledger.PostgisTable{...})`
  - TypeScript：`await client.registerTable(project.id, "roads", { schema: "public", table: "roads", idColumn: "id", geometryColumn: "geom" })`
- **HTTP API / CLI**：调用 `create_dataset` 操作并传入 `postgis_table` 对象：

```json
{
  "project": "0192d4a0-0000-7000-8000-000000000001",
  "name": "roads",
  "postgis_table": {
    "schema": "public",
    "table": "roads",
    "id_column": "id",
    "geometry_column": "geom"
  }
}
```

注册成功后，GeoLedger 会在项目中生成初始修订（提交说明为 `Register table`），并返回包含 `postgis_table` 绑定详情与源表 `crs` 的数据集信息。

## 步骤 3：为大表配置 GiST 空间索引

为了避免在注册阶段对存量超大表产生长时间建索引阻塞，**GeoLedger 不会在纳管时自动为外部源表创建空间索引**。如果你的业务需要按空间范围（`bbox`）查询该数据集，请由表所有者预先或在维护窗口内为源表几何列创建 `GiST` 索引，并通过 `EXPLAIN` 验证查询计划：

```sql
CREATE INDEX IF NOT EXISTS roads_geom_gist
  ON public.roads USING gist (geom);
```

## 步骤 4：验证工作区编辑、原表写回与历史读取

完成绑定后，建议在测试环境中执行一次端到端验证：

1. **读取源表要素**：通过控制台或 `features` 接口读取几条要素，确认主键值、整数/小数属性精度、几何坐标及原始 `crs` 与源表完全一致。
2. **通过工作区发布修改**：创建一个工作区，修改其中一条测试要素的属性并保存。此时直接用 SQL 查询 `public.roads` 原表，验证**未发布草稿不会污染原表**。
3. **验证原子发布写回**：将工作区发布为新修订后，同时核对以下三处结果：
   - 直接用 SQL 查询 `public.roads`，确认该行已更新为新属性值，且几何 SRID 未被改变。
   - 指定新修订号查询 GeoLedger `features`，返回更新后的要素。
   - 指定初始修订号查询 GeoLedger `features`，引擎自动从 `gl_history` 归档记录中还原并返回修改前的旧状态。

## DBA 须知：源表透明度、锁机制与防漂移底层

为了让数据库管理员（DBA）对生产数据库中的对象变化拥有 100% 的知情权与控制权，GeoLedger 在纳管业务表时遵循透明、确定且最小侵入的工程原则：

### 1. 表锁级别与事务安全

- **纳管初始化阶段**：执行 `LOCK TABLE <table> IN SHARE ROW EXCLUSIVE MODE`。该锁级别允许外部只读查询并发进行，但会阻断并发写入与外部 DDL，确保在初始化扫描与安装触发器期间表结构不发生并发漂移。
- **运行期间读写校验**：在每次读取或发布准备阶段，GeoLedger 仅获取轻量级的 `LOCK TABLE <table> IN ACCESS SHARE MODE`，与普通 SQL `SELECT` 互不阻塞。

### 2. 窄 ID 排序索引（`gl_order_*`）

为了在进行全表有界分页（`source_page` 游标扫描）时保证跨多事务的绝对顺序稳定且不依赖系统 Locale，GeoLedger 会检查源表主键上是否存在 C 排序规则（`"C" collation`）的 B-tree 索引。若尚未建立，系统会自动创建窄索引：

```sql
CREATE INDEX "gl_order_<uuid>" ON public.roads ((id::text COLLATE "C"));
```

DBA 可在数据库中查看到以 `gl_order_` 为前缀的索引，该索引仅占用主键文本表示的空间，且在调用 `delete_dataset` 解除纳管时会自动同步删除。

### 3. 三大保护触发器与防漂移机制（Drift Detection）

GeoLedger 在源表上挂接以下三个专用触发器，并在元数据表 `gl_source_state` 中对触发器和表对象的 `relfilenode`、`oid` 及 `xmin` 建立数字指纹（`stamp`）：

| 触发器名称 | 执行时机与作用 | 启用级别与防篡改 |
|---|---|---|
| `gl_versioned_write` | `BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE`（语句级）调用 `public.gl_source_guard()` | 状态为 Origin，直接拦截任何绕过 GeoLedger 的普通外部 SQL 直接写操作 |
| `gl_versioned_track` | `AFTER INSERT OR UPDATE OR DELETE`（行级）调用 `public.gl_source_track('<pk>')` | 设置为 `ENABLE ALWAYS`，即使在逻辑复制或特殊会话下也能精准捕获行级变更 |
| `gl_versioned_truncate` | `AFTER TRUNCATE`（语句级）调用 `public.gl_source_track()` | 设置为 `ENABLE ALWAYS`，严防源表被外部清空 |

每个触发器均打上带有数据集 UUID 的注释标签（`COMMENT ON TRIGGER ... IS 'geoledger:<uuid>'`）。

在每次通过工作区向源表写入前，GeoLedger 均会执行 `ensure_source_clean` 检查。若检测到以下任何一种异常，系统将立即阻断写入并返回 `409 Conflict ("business table changed outside GeoLedger; reconcile the source before publishing")`：
- 源表字段类型、列数、几何类型或 SRID 被外部 DDL 变更；
- 保护触发器被外部命令禁用、删除或修改；
- 变更跟踪表（`gl_source_changes`）中记录到了非 GeoLedger 发起的外部写操作。

## 存量表运维与生命周期注意事项

- **写入保护与防漂移检查**：业务表被纳管期间，所有业务增删改都应通过 GeoLedger 工作区发布。源表上的保护触发器会拦截绕过 GeoLedger 的普通 SQL 直接写入；同时，GeoLedger 在读取和发布前会校验绑定表的 OID、列结构签名与变更跟踪表（`gl_source_track`）。若检测到表结构被私自篡改或触发器被绕过，系统将明确拒绝读写以保护数据完整性，而不会静默覆盖数据。
- **解除绑定（删除数据集或项目）**：当在 GeoLedger 中调用 `delete_dataset` 或 `delete_project` 时，系统会移除保护触发器并清理 GeoLedger 内部的版本历史记录，但**原有的 PostGIS 业务表及其当前最新数据会完好保留**。
- **备份与跨环境迁移差异**：
  - **PostgreSQL 原生备份（`pg_dump` / PITR）**：必须将源业务表、GeoLedger 系统表（`gl_*`）与触发器放在同一个数据库备份中一并恢复。
  - **逻辑导出与导入（`export` / `import`）**：逻辑导出包含完整版本数据，但 `import` 到新环境时会将其恢复为 GeoLedger **内部自建数据集**，不会自动跨库重建外部业务表绑定。详见 **[备份、导出与恢复]({{< relref "/docs/operations/backup/" >}})**。

## 实现依据

- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/session/tables.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/session/tables.rs)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
- [docs/storage.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/storage.md)
