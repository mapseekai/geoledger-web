---
title: "整体架构"
description: "了解接入层、统一业务应用、纯合并核心和事务存储的职责。"
weight: 10
lastmod: 2026-10-29
---

GeoLedger 是按职责划分模块的 Rust 服务。HTTP 与 gRPC 入口共享 Application；SQLite / SpatiaLite 与 PostGIS 是服务端选择的可替换后端。

## 调用关系

{{< architecture >}}

架构图中的框代表职责，不代表每个框都要独立部署。`geoledger-core` 是 Application 调用的纯合并依赖，不是串在数据库前面的网络服务。

## 接入层：不同协议，同一规则

浏览器通过 Next.js BFF 发起私有 Session HTTP 请求；CLI 与四语言 SDK 通过 gRPC 接入；外部 HTTP 客户端使用公开 Bearer API Key 接口。

服务端适配器负责传输、认证、TLS / mTLS、资源预算与请求期限。项目角色、编辑校验和发布业务规则由 Application 统一执行，避免 HTTP 与 gRPC 各维护一套行为。

## 应用层与纯核心

`geoledger-engine::Application` 编排身份、项目、数据集、工作区、查询、冲突、发布、历史和审计。它拥有事务生命周期，将业务操作映射为语义化存储能力。

`geoledger-core` 包含与数据库和传输无关的 Record、Cell 与三方合并逻辑。Application 负责取得 Base、Current 与 Draft、调用合并规则、校验候选，再交给存储事务暂存和提交。

## 存储边界

`StorageBackend::begin` 返回 `RepositoryTransaction`。事务由 Credential、Project、Dataset、Workspace、Feature、History、Publication、Audit 等能力组合而成，借用同一连接、快照、锁、期限与响应预算。

按能力拆分不等于拆成多个事务。领域函数只依赖需要的接口，最终只有事务所有者能调用消耗所有权的 `commit`。

## 源码地图

| 目录 | 职责 |
|---|---|
| `crates/core` | 数据模型与三方合并 |
| `crates/engine` | Application、业务编排与存储契约 |
| `crates/engine/src/session` | SQL 适配、事务、原生存储与数据运维 |
| `crates/spatialite` | SpatiaLite 原生连接与几何运行时 |
| `crates/server`、`crates/rpc` | HTTP / gRPC、配置与传输安全 |
| `crates/cli`、`sdk` | 远程客户端与四语言 SDK |
| `web` | Next.js BFF、地图与控制台界面 |

## 部署边界

仓库的统一镜像包含服务端、CLI、控制台及 SpatiaLite 运行依赖。逻辑分层不要求拆成多个容器；独立部署时仍需保留私有 BFF 到服务端的信任边界。

进一步阅读[版本模型]({{< relref "/docs/architecture/version-model/" >}})、[存储布局]({{< relref "/docs/architecture/storage/" >}})和[事务与发布恢复]({{< relref "/docs/architecture/transactions/" >}})。

## 实现依据

- [README.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/README.md)
- [crates/core/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/core/src/lib.rs)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/lib.rs)
- [crates/engine/src/repository.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/repository.rs)
- [docs/storage.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/storage.md)
