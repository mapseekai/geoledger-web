---
title: "认识 GeoLedger：核心对象与边界"
linkTitle: "认识 GeoLedger"
description: "理解项目、数据集、要素、工作区和共享修订之间的关系。"
weight: 10
lastmod: 2026-10-29
doc_type: explanation
---

GeoLedger 是基于 Rust 的空间要素版本管理与协作编辑服务。编辑人员在工作区准备增量，通过差异审阅、三方合并和原子发布形成项目级共享修订。

## 适用工作流

道路、管线、设施等持续维护的数据，可以按一次业务更新组织跨数据集修改。控制台负责地图交互与审阅；HTTP、CLI 与 SDK 将同一流程接入已有系统。

空间数据库保存与查询数据，GeoLedger 组织变更的基线、草稿、发布和历史。协作以工作区和发布为边界，当前能力不包含基于 CRDT 的实时节点协同。

## 术语表

| 术语 | 含义 | 接入时的约束 |
|---|---|---|
| 项目 Project | 数据集、成员、工作区与修订的组织边界 | HEAD 属于项目 |
| 数据集 Dataset | 声明几何类型、坐标维度与 CRS 的要素集合 | 名称与稳定数据集 ID 分离 |
| 要素 Feature | 含属性和几何的 GeoJSON Feature | 使用稳定字符串 ID |
| 工作区 Workspace | 固定基础修订上的草稿增量 | 可以覆盖项目内多个数据集 |
| 修订 Revision | 发布形成的共享数据版本 | 用于固定读取与追溯 |
| HEAD | 项目当前共享修订的高水位 | 其他工作区发布时可推进 |
| 基础修订 base_revision | 开始或更新基准时采用的共享状态 | 不随 HEAD 自动变化 |
| 编辑版本 version | 工作区草稿自身的乐观并发版本 | 写操作携带预期版本 |
| 字段定义 Schema | 数据集普通属性字段的版本化定义 | 与同一修订或工作区的要素配套读取 |

例如，道路与设施可以在同一个工作区编辑，随后进入同一个修订。要素 ID、数据集 ID 和项目 ID 分别标识不同层次的对象。

## 后端与接入边界

SQLite + SpatiaLite 适用于单机运行与本地验证；PostgreSQL + PostGIS 支持连接池、原生空间类型与已有业务表纳管。两种后端由服务端配置选择，共享 Application 和业务协议。

客户端访问服务端。工作区保存增量，历史保留必要的旧正文；要素正文保存在数据库中。PostGIS 连接失败会作为配置或存储错误返回，不自动切换到另一个 SQLite 数据库。

## 继续阅读

初次使用继续[快速开始]({{< relref "/docs/start/quickstart/" >}})。需要分析读取结果时，阅读[版本与可见性模型]({{< relref "/docs/architecture/version-model/" >}})；评估系统边界时，阅读[整体架构]({{< relref "/docs/architecture/overview/" >}})。

## 实现依据

- [README.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/README.md)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/lib.rs)
- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
