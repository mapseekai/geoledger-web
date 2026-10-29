---
title: "运维指南"
description: "配置部署、管理身份、准备备份和诊断服务故障。"
weight: 50
lastmod: 2026-10-29
icon: fa-solid fa-server
cascade:
  doc_type: howto
  ui:
    section_index: list
---

运维指南面向负责服务与数据库的操作人员。先核对[版本与存储兼容性]({{< relref "/docs/reference/compatibility/" >}})，在隔离环境验证部署、权限与恢复流程，再用于目标环境。

配置键的默认值由[配置参考]({{< relref "/docs/reference/configuration/" >}})统一维护。发布调用的结果未知时，使用[发布恢复指南]({{< relref "/docs/guides/publication-recovery/" >}})；启动、登录和容量问题见[故障诊断]({{< relref "/docs/operations/troubleshooting/" >}})。
