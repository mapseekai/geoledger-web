---
title: "整体架构与模块边界"
linkTitle: "整体架构"
description: "解析 GeoLedger 的多协议接入层、统一领域应用层（Application）、纯合并核心（geoledger-core）与可替换事务存储后端。"
weight: 10
lastmod: 2026-10-29
---

GeoLedger 是一个按职责清晰分层的 Rust 空间版本管理服务。无论是来自浏览器的交互操作、来自 CLI 与四语言 SDK 的 gRPC 调用，还是来自外部业务系统的 HTTP 请求，最终都汇入同一个领域应用层（`geoledger-engine::Application`），共享完全一致的权限模型、三方合并规则与单事务存储语义。

## 系统模块与调用拓扑

{{< architecture >}}

> **阅读架构图的提示**：上图中的方框代表代码模块与职责边界，而非必须拆分部署的微服务网络拓扑。在实际运行中，`geoledger-core` 是被 `Application` 直接在进程内存中调用的纯计算库，`StorageBackend` 则是连接 SQLite 或 PostgreSQL 的进程内存储适配器。

## 1. 传输与接入层：多协议入口，同一套领域规则

GeoLedger 支持三种客户端接入路径，由 `crates/server` 与 `crates/rpc` 中的传输适配器统一处理协议编解码、TLS / mTLS 握手、并发准入信号量、请求/响应字节预算预留以及总期限（Deadline）控制：

- **Web 控制台（Next.js BFF + 私有 Session HTTP）**：浏览器仅持有加密的 `HttpOnly` 会话 Cookie，通过 Next.js 服务端 BFF 向 `geoledger-server` 发起受 Origin 保护的私有会话请求。
- **gRPC 接口（`geoledger.v1`）**：供远程命令行工具 `gl` 与 Rust、Go、TypeScript / Node.js、Python 四语言 SDK 接入，支持大数据量的 `SaveStream` 与 `FeaturesStream` 分块流式传输。
- **公开 HTTP 业务 API（`POST /api/v1/{operation}`）**：面向第三方系统提供标准 Bearer API Key 认证与 JSON 请求/响应接口。

传输层本身不包含任何业务状态分支——一旦请求通过认证准入，所有项目 RBAC 校验、几何规范检查、冲突计算与发布编排全部交由 `Application` 统一执行，从根源上杜绝了“HTTP 与 gRPC 行为不一致”的风险。

## 2. 领域应用层（`Application`）与纯合并核心（`geoledger-core`）

为了保持领域逻辑的高可测试性与存储无关性，核心引擎拆分为两个 crate：

- **`geoledger-core`（纯函数式合并核心）**：
  完全不依赖任何数据库驱动、网络协议或异步运行时。它定义了基础的 `Record`、`Cell` 数据结构以及**属性级三方合并**（Three-Way Merge）算法。给定共同基线（`Base`）、当前共享状态（`Current`）和工作区草稿（`Draft`），它纯确定性地计算出合并后的候选要素或字段级冲突清单。
- **`geoledger-engine::Application`（业务与事务编排层）**：
  负责用户与凭据管理、项目与成员治理、数据集与版本化字段（Schema）、工作区草稿保存、空间与历史查询、发布编排以及审计记录。`Application` 是**数据库事务的唯一所有者**：它在操作开始时开启事务，按需借用语义化仓储接口完成读取、调用 `geoledger-core` 合并、校验响应字节预算，并在一切无误后执行唯一一次 `commit`。

## 3. 按能力拆分的存储边界（`RepositoryTransaction`）

在 `crates/engine/src/repository.rs` 中，存储后端契约按领域职责拆分为十余个细粒度 Trait：

- **后端生命周期与运维**：`StorageBackend`（初始化、健康检查、连接池指标、开启事务）与 `StorageMaintenance`（在线物理备份 `backup`、可移植逻辑导出 `export` 与导入 `import`）。
- **事务内语义化能力**：`CredentialRepository`、`ProjectRepository`、`DatasetRepository`、`WorkspaceRepository`、`FeatureRepository`、`HistoryRepository`、`PublicationRepository`、`AuditRepository`、`PostgisTables` 与 `ResponseBudget`。

当 `StorageBackend::begin` 返回一个 `RepositoryTransaction` 时，上述所有能力都在**同一个底层数据库事务对象**（`SqlTransaction`）上实现：

- 它们共享同一个数据库连接、同一个一致性读快照、同一组行级/咨询锁、同一个截止时间（Deadline）以及同一个事务内合并暂存区（Merge Stage）。
- 领域函数只需通过 `&mut (impl WorkspaceRepository + AuditRepository + ?Sized)` 借用自己所需的最小能力集合，既便于编写轻量级单元测试，又从类型系统层面禁止了任何子函数私自提前提交或另开连接写审计日志。

## 4. 源码仓库目录地图

| 源码路径 | 核心职责说明 |
|---|---|
| `crates/core` | 与存储和网络无关的 `Record` / `Cell` 模型及纯三方合并算法 |
| `crates/engine` | `Application` 业务编排、权限与几何校验、Schema 演进及 `repository` 存储契约定义 |
| `crates/engine/src/session` | SQLite 与 PostgreSQL/PostGIS 的统一 SQL 事务适配器、原生表纳管与可移植导入导出 |
| `crates/spatialite` | SQLite 的 SpatiaLite 5 原生扩展安全加载器与空间几何运行时 |
| `crates/server` · `crates/rpc` | HTTP / gRPC 监听器、TLS 热重载、内存与并发预算、Prometheus 指标与本地数据运维 CLI |
| `crates/cli` · `sdk/*` | 远程命令行客户端 `gl` 以及 Rust、Go、TypeScript / Node.js、Python 四语言官方 SDK |
| `web` | 基于 Next.js 的 Web 控制台、BFF 会话代理、地图工作台与版本演进图组件 |

## 5. 灵活的部署拓扑

逻辑上的清晰分层并不意味着沉重的运维负担。GeoLedger 官方提供的统一容器镜像将 `geoledger-server`、`gl` CLI、Next.js standalone 控制台与 SpatiaLite 运行时打包在单个非 root 镜像中，开箱即可单容器运行；而在高并发生产环境中，你也可以无缝切换至外部托管的 PostgreSQL + PostGIS 集群并前置 Nginx / Caddy TLS 网关（详见 **[部署与运行指南]({{< relref "/docs/operations/deployment/" >}})**）。

## 继续阅读

- 深入了解工作区与历史快照如何隔离与读取：**[版本与可见性模型]({{< relref "/docs/architecture/version-model/" >}})**
- 了解并发编辑如何自动合并与裁决：**[三方合并与冲突处理]({{< relref "/docs/architecture/merge/" >}})**
- 了解存储格式 `19` 的物理表与历史区间设计：**[空间存储与历史布局]({{< relref "/docs/architecture/storage/" >}})**
- 了解原子发布与断连重放原理：**[事务与发布一致性]({{< relref "/docs/architecture/transactions/" >}})**

## 实现依据

- [README.md](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/README.md)
- [crates/core/src/lib.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/core/src/lib.rs)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/engine/src/lib.rs)
- [crates/engine/src/repository.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/engine/src/repository.rs)
- [docs/storage.md](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/docs/storage.md)
