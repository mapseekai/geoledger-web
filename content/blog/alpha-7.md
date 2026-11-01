---
title: "v0.3.0-alpha.7 发布：每数据集独立分表与版本化字段定义"
description: "引入存储格式 19：为每个自建数据集分配独立物理表与空间索引，支持在工作区中版本化增删普通属性字段并与要素修改同事务原子发布。"
summary: "引入存储格式 19：为每个自建数据集分配独立物理表与空间索引，支持在工作区中版本化增删普通属性字段并与要素修改同事务原子发布。"
weight: 10
lastmod: 2026-10-29
date: 2026-10-26T23:21:21+08:00
tags: [Release, Schema, PostGIS]
---

**正式发布（Release） · 2026-10-26 · 标签 `v0.3.0-alpha.7`（提交 `f0109c8`）**

`v0.3.0-alpha.7` 是 GeoLedger 存储与数据模型的一次重要演进。本次更新将存储格式推进至 **Format `19`**，核心围绕三项能力展开：**每个自建数据集拥有独立的物理数据表与空间索引**、**数据集普通属性字段（Schema）正式纳入工作区与修订历史管理**，以及 **PostGIS 存量表零拷贝纳管与批量发布优化**。

## 1. 每个自建数据集拥有独立的物理正式表

在 SQLite + SpatiaLite 与 PostgreSQL + PostGIS 双后端下，所有自建数据集现在均采用按数据集分表存储（`gl_data_<随机标识>`）：

- **物理隔离与独立索引**：同一个项目中的道路、建筑、监测点等数据集（包括相同几何类型的多个数据集）各自拥有独立的物理表与空间索引（RTree 或 GiST），并通过 `gl_datasets.storage_table` 维护映射关系，重命名数据集显示名称无需重建物理表。
- **紧凑的增量历史布局**：当前正式表（或纳管的 PostGIS 业务原表）仅存放最新 `HEAD` 下存活的要素；`gl_history` 表仅在要素被修改或删除时归档被替换下来的旧正文；`gl_commit_changes` 则仅记录变更要素的 ID 与增删改标记。发布、删除清理与可移植逻辑导入（`import`）均在单个数据库事务内同步维护物理表与版本记录。

## 2. 版本化字段定义（Schema）与原子保存

数据集的属性表结构演进现在与要素修改共享同一套工作区与修订工作流：

- **按修订或工作区查询 Schema**：新增 `schema` / `Schema` 接口，支持按固定历史 `revision` 或开放 `workspace` 读取字段定义列表（`fields[{name, type, nullable, editable}]`）。
- **原子保存要素与字段意图**：四语言 SDK 新增 `save_changes` / `SaveChanges` / `saveChanges` 方法（HTTP 为 `save.schema_edits`），支持在工作区中声明普通可空字段的新增（`string`、`number`、`integer`、`boolean`、`json`）与删除（`drop`），并与同批要素修改在同一个 `expected_workspace_version` 下原子保存。
- **完整的三态意图与差异展示**：省略 `schema_edits` 表示保留已保存意图，显式传入空数组 `[]` 表示撤销全部未发布字段意图（草稿中被隐藏的原字段值可无损恢复）。`diff`、`commit` 与汇总接口（`workspace_summary` / `commit_summary`）均新增独立的 `schema_changes` 字段，Web 控制台支持直接审阅并发布纯字段变更。

## 3. PostGIS 存量表零拷贝纳管与发布批处理优化

- **零拷贝快速注册**：纳管已有 PostGIS 业务表时，系统仅记录表绑定元数据、初始修订号、保护触发器并在需要时建立窄 ID 排序索引，以有界分页只读校验源表几何，**不再逐行复制原表属性与几何正文**。后续发布仅将受影响行的旧正文归档至历史表，未修改的存量行继续只保存在原业务表中。
- **批量合并与归档**：PostGIS 纳管表发布时按合并页批量读取基础版本与当前版本，并按数据集批量归档旧正文、减少重复几何序列化，在严格保持 64 位数值精度、历史半开区间与响应字节预算的前提下显著减少了项目锁内的逐行 SQL 往返。

## 4. 升级与兼容性必读（Breaking Changes）

> **重要升级提示**：
> 1. **存储格式升级为 `19`**：本版本要求初始化全新的数据目录或空数据库，**明确拒绝直接挂载格式 `16` / `18` 的旧数据库或导入旧格式逻辑导出**。升级前请完整保留旧版服务程序、旧数据库及独立备份，在隔离环境中验证迁移方案。
> 2. **存储扩展接口按能力拆分**：若你维护了自定义 Rust 存储后端适配器，请将原 `RepositoryTransaction` 的方法按领域能力迁入 `CredentialRepository`、`DatasetRepository`、`WorkspaceRepository`、`PublicationRepository` 等子 Trait（详见 **[空间存储与历史布局]({{< relref "/docs/architecture/storage/" >}})**）。

## 延伸阅读

- 操作指南：**[新增与删除版本化字段]({{< relref "/docs/guides/schema/" >}})** · **[纳管已有 PostGIS 业务表]({{< relref "/docs/guides/postgis/" >}})**
- 架构解析：**[空间存储与历史布局]({{< relref "/docs/architecture/storage/" >}})**
- 源码变更记录：[CHANGELOG.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/CHANGELOG.md)
