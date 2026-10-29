---
title: "概念与架构"
description: "理解版本可见性、三方合并、空间存储与发布事务的设计边界。"
weight: 40
lastmod: 2026-10-29
icon: fa-solid fa-diagram-project
cascade:
  doc_type: explanation
  ui:
    section_index: list
---

建议先阅读[核心对象]({{< relref "/docs/start/introduction/" >}})，再从整体架构进入版本模型、合并、存储与事务边界。

本组解释实现为何这样组织，以及这些选择对接入和运行的影响。操作步骤由[操作指南]({{< relref "/docs/guides/" >}})和[运维指南]({{< relref "/docs/operations/" >}})维护。
