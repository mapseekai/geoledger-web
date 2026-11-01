---
title: "空间存储布局与历史归档设计"
linkTitle: "空间存储与历史布局"
description: "深入解析存储格式 19 的每数据集独立分表架构、增量历史归档、SQLite/PostGIS 双后端索引机制以及自定义存储适配器契约。"
weight: 40
lastmod: 2026-11-01
---

在设计空间数据的版本存储时，如果每次发布都把整张图层复制一份全量快照，存储空间与写入时间都会随数据集规模急剧膨胀；反之，如果把所有要素的所有历史版本混杂在单张大表中，又会拖慢高频的当前最新状态（`HEAD`）查询。

GeoLedger 的**存储格式 `19`** 采用 **“当前状态分表存储 + 增量旧正文按需归档”** 的架构：每个数据集拥有独立的物理正式表与原生空间索引，而历史表（`gl_history`）仅在要素被修改或删除时归档被替换下来的旧正文。

## 1. 数据流转与物理存储布局

{{< storage-flow >}}

> **单事务同步保证**：上图中围绕“合并暂存区（Merge Stage）”的所有写入箭头均发生在**同一个数据库事务**内部，不存在后台异步复制延迟或最终一致性窗口。

## 2. 自建数据集的独立物理表设计

每当调用 `create_dataset` 创建一个原生数据集时，即使尚未写入任何要素，GeoLedger 也会立即在当前事务内为其创建一张独立的物理数据表 `gl_data_<随机标识>` 及配套的空间索引，并在元数据表 `gl_datasets.storage_table` 中记录逻辑数据集 UUID 到物理表名的映射：

- **显示名称与物理表解耦**：数据集的显示名称可以包含中文、空格并随时通过 `rename_dataset` 修改，底层物理表名始终保持稳定，无需在重命名时锁表重建。
- **双轨几何存储（精确快照 + 原生空间索引）**：
  - `feature_id` 为表主键。
  - `properties` 保存 UTF-8 JSON 属性文本，保留受支持的 64 位整数精度；JSON 对象字段的原始顺序不是读写契约。
  - `geometry_json` 保存规范化后的原始 GeoJSON 几何文本，用于无损读取响应、版本差异对比与跨后端逻辑导出。
  - **原生几何列（`geom` / `geom_z`）**：专门服务于空间包络框（`bbox`）索引检索。

## 3. SQLite + SpatiaLite 与 PostgreSQL + PostGIS 实现对比

两种存储后端共享完全相同的上层领域逻辑与 SQL 事务适配器（`crates/engine/src/session`），同时充分利用各自数据库的空间引擎特性：

| 技术维度 | SQLite + SpatiaLite 5 | PostgreSQL + PostGIS |
|---|---|---|
| **原生几何表示** | 注册 SpatiaLite `geom`（XY）与 `geom_z`（XYZ）二进制几何列 | 原生 PostGIS `geometry` 列（自建表派生索引采用 `SRID 0` 平面计算，纳管原表保留源表 `SRID`） |
| **空间索引与 `bbox` 过滤** | 标准 RTree 空间索引初筛候选集 + SpatiaLite `ST_Intersects` 精确判定 | 原生 `GiST` 空间索引直接过滤几何列（查询时无需反序列化 JSON） |
| **并发与写锁机制** | `WAL` 模式 + `synchronous = FULL`；写事务采用 `BEGIN IMMEDIATE` 串行化 | 数据库连接池（默认 20）+ 项目级行锁 / 咨询锁（Advisory Lock）与工作区级行锁 |
| **一致性读快照** | `query_only` 事务一致性快照 | `REPEATABLE READ` 只读事务隔离级别 |
| **外部存量表纳管** | 不涉及（支持通过 GeoJSON 导入创建内部表） | 支持零拷贝绑定同库既有 PostGIS 业务表，发布时同事务写回原表并校验延迟约束与保护触发器 |

> **关于自建表 `SRID 0` 的说明**：在自建数据集中，GeoLedger 将数据集声明的坐标系（如 `EPSG:4326`、`EPSG:3857` 或自定义 WKT）完整保存在 `gl_datasets.crs` 中，而内部派生的空间索引列统一使用 `SRID 0` 在该数据集自身的坐标空间内执行平面矩形相交计算。这意味着系统**绝不会在底层擅自将你的地方坐标系数据转换成 WGS 84**，所有读写与 `bbox` 查询均严格保持原始坐标数值。

## 4. 增量历史归档与提交明细分离

为了兼顾历史可追溯性与存储效率，GeoLedger 对历史记录做了精细的职责拆分：

1. **当前正式表（`gl_data_*` 或 PostGIS 原表）**：只存放项目最新 `HEAD` 下仍然存活的要素最新状态，确保最常用的最新数据查询直接命中紧凑的主表与空间索引。
2. **历史旧正文表（`gl_history`）**：**仅在某条要素被修改覆盖或被删除时**，才将该要素被替换前的旧属性与旧几何写入 `gl_history`，并标记其有效修订区间 `[valid_from, valid_to)`。未被修改过的存量要素（包括纳管的数百万行 PostGIS 源表数据）不会在 `gl_history` 中产生任何冗余拷贝。
3. **轻量级提交变更清单（`gl_commit_changes`）**：仅记录每次发布涉及的数据集、要素 `feature_id` 以及增删改分类标记，使得统计汇总（`commit_summary`）与游标探测无需扫描庞大的几何正文。

## 5. 自定义存储后端的扩展契约（Conformance Suite）

如果你希望将 GeoLedger 适配到其他具备 ACID 事务能力的数据库，需要实现 `geoledger_engine::repository` 中定义的仓储能力 Trait，并通过 `Application::with_backend` 接入（参见 **[整体架构]({{< relref "/docs/architecture/overview/" >}})**）。现有 `crates/engine/tests/conformance.rs` 的 fixture 仅选择内置 SQLite 或 PostGIS；新后端需要接入测试 fixture 和服务端选择，运行相同的业务场景，并补充事务失败、锁等待、崩溃恢复与容量测试。一个合格的存储后端必须严格满足以下十项核心不变量：

1. **单事务原子性**：未调用 `commit` 即被丢弃（Drop）的事务对象必须回滚全部写入。
2. **并发锁串行化**：`project_head(lock=true)` 串行化同项目并发发布并在获锁后读取最新 `HEAD`；`workspace_state(write=true)` 串行化同工作区写入。
3. **跨表同提交**：正式要素、历史有效期、提交明细、Schema 历史、`HEAD`、工作区状态、幂等回执与审计记录必须在同一事务内共同提交。
4. **不可变发布回执**：按 `(project, subject, request_id)` 唯一持久保存已提交回执，支持断连重放。
5. **半开区间可见性**：严格按 `valid_from <= revision AND (valid_to IS NULL OR revision < valid_to)` 还原历史快照；删除以旧正文的结束区间、当前行的缺失和提交变更记录表达。
6. **草稿空间遮蔽**：工作区 `bbox` 查询必须先以草稿增量覆盖基线要素，再执行空间过滤，确保已删除或移出范围的草稿遮蔽原位置。
7. **事务私有合并暂存（Merge Stage）**：`begin_merge` 与 `stage` 在事务私有暂存区中验证候选，发布提交后才转为公开历史。
8. **期限（Deadline）传播与确定性报告**：所有锁等待、查询与提交均服从请求剩余期限，并准确区分明确拒绝与结果未知（`uncertain`）。
9. **审计序号单调与提交顺序一致**：同项目的 `append_audit` 必须按实际事务提交顺序分配递增 ID，确保 `audit` 游标分页永不漏读。
10. **同快照仅键续页探测**：`diff_has_after`、`commit_has_after`、`history_has_after` 与 `audit_has_after` 在同一读快照内仅探测后续键以精确判定整页终页。

## 实现依据

- [crates/engine/src/repository.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/repository.rs)
- [crates/engine/src/session/query.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/session/query.rs)
- [crates/engine/tests/conformance.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/tests/conformance.rs)
- [docs/storage.md](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/docs/storage.md)
