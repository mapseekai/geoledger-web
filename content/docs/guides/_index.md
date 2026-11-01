---
title: "操作指南"
description: "围绕具体业务任务的操作手册：涵盖 Web 控制台使用、工作区编辑与冲突解决、PostGIS 存量表纳管、版本化字段增删、历史查询撤销以及发布结果恢复。"
weight: 20
lastmod: 2026-10-29
icon: fa-solid fa-list-check
cascade:
  doc_type: howto
  ui:
    section_index: list
---

本章节面向已经了解 GeoLedger 基本概念的 GIS 编辑人员与应用开发者。每一篇指南均针对一个独立的实际业务场景，详细说明前置条件、标准操作步骤、结果核对方法与常见异常处理。

## 任务速查

- **[Web 控制台导览]({{< relref "/docs/guides/console/" >}})**：熟悉地图工作台、属性表、工作区版本图与提交详情界面，准确切换“已发布数据”与“个人草稿”视图。
- **[工作区编辑、冲突解决与发布]({{< relref "/docs/guides/workspaces/" >}})**：掌握分批保存要素、审阅跨数据集差异、处理共享主线（`HEAD`）推进引发的三方合并冲突以及执行变基（Rebase）。
- **[大规模要素批量导入与分批保存]({{< relref "/docs/guides/batch-ingestion/" >}})**：针对海量要素导入场景，掌握 100 条分片保存、工作区版本递增、拓扑告警捕获与单事务原子发布。
- **[纳管已有 PostGIS 业务表]({{< relref "/docs/guides/postgis/" >}})**：在不复制存量表数据的前提下将 PostgreSQL/PostGIS 中的既有业务表注册为受管数据集，实现事务化同步写回。
- **[新增与删除版本化字段]({{< relref "/docs/guides/schema/" >}})**：在工作区中声明数据集普通属性字段的新增与删除意图，并与要素修改在同一事务内原子发布。
- **[查询历史快照与撤销提交]({{< relref "/docs/guides/history/" >}})**：按固定修订号查询历史时刻的要素与字段结构，或通过 `restore` 生成反向变更工作区安全回退指定提交。
- **[确认与恢复中断的发布]({{< relref "/docs/guides/publication-recovery/" >}})**：当发布请求遭遇网络超时、断连或客户端重启时，利用原始 `request_id` 与持久化意图安全确认最终提交状态。
