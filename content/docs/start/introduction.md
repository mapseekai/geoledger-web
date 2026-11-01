---
title: "认识 GeoLedger：核心概念与系统边界"
linkTitle: "认识 GeoLedger"
description: "快速掌握项目、数据集、空间要素、工作区草稿与项目级共享修订的核心模型。"
weight: 10
lastmod: 2026-11-01
doc_type: explanation
---

在传统的 GIS 数据维护流程中，团队往往面临两难选择：要么通过拷贝整份 GeoJSON / Shapefile 文件来传递修改，难以追踪要素级变化与合并冲突；要么多个客户端直接连入同一张空间数据库表进行读写，一旦出错便难以审计与回滚。

**GeoLedger** 是用 Rust 编写的空间要素版本管理与协作编辑服务。它在空间数据库之上构建了清晰的**草稿工作区**（Workspace）与**共享修订**（Revision）模型，让空间数据的每一次增删改都具备可审阅、可合并、可追溯的版本边界。

## 核心工作流与适用场景

在道路网维护、市政管线更新、环境监测站点管理等持续演进的业务场景中，一次业务变更往往涉及多个图层（例如同时新增一段道路中心线并调整沿线附属设施）。

GeoLedger 的典型协作流程包含四个阶段：

1. **隔离草稿**：编辑人员基于项目当前的共享修订创建一个**工作区**，在工作区内跨一个或多个数据集保存要素的新增、修改、删除或字段定义变更。
2. **差异审阅**：在正式发布前，随时通过要素级差异（Diff）和数据集汇总统计（Summary）检查所有待提交修改，此时线上共享数据完全不受影响。
3. **三方合并**：如果在编辑期间其他团队成员先行发布了新版本，GeoLedger 会基于共同基线（Base）、最新共享状态（Current）与当前草稿（Draft）执行**属性级三方合并**，自动合入互不冲突的属性修改，并将冲突字段或几何变化清晰地呈现给审阅者裁决。
4. **原子发布**：确认无误后执行发布（Publish）。正式数据表更新、历史旧正文归档、字段历史、项目 `HEAD` 推进、幂等回执与审计日志在同一数据库事务中原子提交。

> **设计边界说明**：GeoLedger 以“工作区草稿 + 事务化发布”作为协作边界，专注于数据一致性、明确审阅和可审计历史，当前不包含基于 CRDT 的多光标毫秒级实时协同绘制。

## 核心对象与术语表

理解以下概念有助于你快速掌握控制台操作与 API 契约：

| 核心术语 | 英文标识 | 概念说明 | 关键契约与约束 |
|---|---|---|---|
| **项目** | `Project` | 数据集、团队成员、工作区、版本历史与审计日志的顶层组织边界 | 共享修订号（`HEAD`）在项目级别全局递增 |
| **数据集** | `Dataset` | 声明了固定几何类型（`point` / `line` / `polygon`）、坐标维度（`2` 或 `3`）和坐标系（`crs`）的要素集合 | 显示名称可随时重命名，底层使用稳定的数据集 UUID 与独立物理表 |
| **要素** | `Feature` | 符合 GeoJSON 结构的空间记录，包含 `id`、`properties` 与 `geometry` | 由数据集内唯一的稳定字符串 `id` 标识；写入时提交完整 Feature |
| **工作区** | `Workspace` | 建立在固定基础修订之上的个人草稿容器 | 一个工作区可同时包含同一项目下多个数据集的草稿修改 |
| **共享修订** | `Revision` | 每次工作区成功发布后生成的项目版本号（如 `1`、`2`、`3`） | 历史仍存在时，可指定 `revision` 读取一致性快照；删除数据集或项目可能清理相关历史 |
| **项目主线高水位** | `HEAD` | 项目当前最新已发布的共享修订号 | 初建空项目时为 `0`；每当任意工作区发布成功即向前推进 |
| **基础修订** | `base_revision` | 工作区创建或执行变基（Rebase）时所锚定的共享修订号 | 不会随他人发布而静默改变；主动变基时更新 |
| **草稿编辑版本** | `version` | 工作区自身的乐观并发控制计数器（从 `0` 开始递增） | 每次保存、解决冲突、变基或发布请求均需携带 `expected_workspace_version` |
| **版本化字段定义** | `Schema` | 数据集普通属性字段（名称、类型、可空性、可编辑性）的版本化结构描述 | 支持在工作区中声明字段的新增与删除，并随要素一同发布与按修订查询 |

## 双存储后端与多协议接入

GeoLedger 将领域规则与底层存储解耦，服务端启动时可通过 `GL_STORAGE` 选择存储引擎：

- **SQLite + SpatiaLite（默认）**：开箱即用的单机空间存储引擎，采用 WAL 模式、SpatiaLite 原生几何与 RTree 空间索引，非常适合本地开发、功能验证与中小型单机部署。
- **PostgreSQL + PostGIS**：面向多用户并发协作与生产环境的企业级后端，支持连接池、原生 `geometry` 列与 GiST 空间索引，并支持**直接纳管数据库中已有的业务表**，在保留源表坐标系（SRID）的前提下将发布结果同事务写回原表。

在客户端接入层，所有入口均汇入同一个 `geoledger-engine::Application`：

- **Web 控制台**：内置地图工作台、图层树、属性表、版本演进图与可视化冲突解决界面（通过 Next.js BFF 私有会话传输与后端通信）。
- **gRPC 与四语言 SDK**：提供 Rust、Go、TypeScript / Node.js、Python 官方客户端及远程命令行工具 `gl`。
- **HTTP 业务 API**：提供基于 Bearer API Key 的 `POST /api/v1/{operation}` JSON 接口，便于第三方业务系统快速集成。

## 下一步

- 准备动手实践？请前往 **[快速开始：启动测试环境]({{< relref "/docs/start/quickstart/" >}})**。
- 想深入了解工作区与历史修订的读取原理？请阅读 **[版本与可见性模型]({{< relref "/docs/architecture/version-model/" >}})**。
- 想从全局视角审视模块职责？请浏览 **[整体架构]({{< relref "/docs/architecture/overview/" >}})**。

## 实现依据

- [README.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/README.md)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/lib.rs)
- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
