---
title: "概念与架构"
description: "深入理解 GeoLedger 的分层架构、版本与可见性模型、属性级三方合并算法、空间存储布局以及单事务一致性边界。"
weight: 40
lastmod: 2026-10-29
icon: fa-solid fa-diagram-project
cascade:
  doc_type: explanation
  ui:
    section_index: list
---

本章节从系统设计与工程实现的角度，深入解析 GeoLedger 如何在标准空间数据库（SQLite + SpatiaLite 与 PostgreSQL + PostGIS）之上构建可靠的版本控制、三方合并与事务一致性保证。

如果你是初次接触 GeoLedger，建议先阅读 **[认识 GeoLedger：核心概念与系统边界]({{< relref "/docs/start/introduction/" >}})**，再按以下顺序深入各专题：

1. **[整体架构]({{< relref "/docs/architecture/overview/" >}})**：了解多协议接入层、统一业务应用层（`Application`）、纯函数式合并核心（`geoledger-core`）与事务化存储后端（`RepositoryTransaction`）的职责划分。
2. **[版本与可见性模型]({{< relref "/docs/architecture/version-model/" >}})**：剖析项目 `HEAD`、工作区基础修订（`base_revision`）、草稿编辑版本（`version`）与历史区间（`valid_from` / `valid_to`）的快照读取语义。
3. **[三方合并与冲突处理]({{< relref "/docs/architecture/merge/" >}})**：理解为何采用属性级三方合并搭配整体几何比较，以及冲突裁决上下文（`stale_resolution`）与字段变更的并发边界。
4. **[空间存储与历史布局]({{< relref "/docs/architecture/storage/" >}})**：解析存储格式 `19` 的每数据集独立分表设计、增量历史归档、原生空间索引（RTree / GiST）与新存储后端的扩展契约。
5. **[事务与发布一致性]({{< relref "/docs/architecture/transactions/" >}})**：探究单一事务所有者模式、项目与工作区并发锁协调、编码内存预算控制以及网络断连下的不可变幂等发布回执机制。
