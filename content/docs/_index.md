---
title: "文档"
description: "学习发布流程、完成编辑任务、查阅接口契约与理解架构。"
weight: 10
lastmod: 2026-10-29
type: docs
icon: fa-solid fa-book-open
sidebar_root_for: self
sidebar_root_link_self: true
cascade:
  type: docs
  footer_style: slim
  reading_time: false
---

GeoLedger 通过工作区组织空间要素修改，经差异审阅与合并后发布为项目级修订。根据当前任务选择入口。

## 从一个任务开始

- 第一次使用：从[快速开始]({{< relref "/docs/start/quickstart/" >}})启动测试环境，再[完成第一次发布]({{< relref "/docs/start/first-publication/" >}})。
- 接入应用：完成 [Python SDK 教程]({{< relref "/docs/start/sdk/" >}})，再查阅 [HTTP]({{< relref "/docs/reference/http/" >}})、[SDK]({{< relref "/docs/reference/sdk/" >}})与[分页契约]({{< relref "/docs/reference/pagination/" >}})。
- 维护已有数据：阅读[工作区编辑]({{< relref "/docs/guides/workspaces/" >}})、[PostGIS 表纳管]({{< relref "/docs/guides/postgis/" >}})或[字段变更]({{< relref "/docs/guides/schema/" >}})。
- 部署与排障：从[运维指南]({{< relref "/docs/operations/" >}})选择部署、凭据管理、备份或故障诊断。

## 文档的四种用途

**教程**提供有起点和结果的学习流程；**操作指南**解决具体任务，运维指南属于这一类；**技术参考**定义请求、配置与兼容性；**概念与架构**解释版本语义和设计取舍。

本站依据固定源码编写。开始运行命令前，请核对[版本、兼容性与验证范围]({{< relref "/docs/reference/compatibility/" >}})。发布公告与主分支记录分别保存在 [Blog]({{< relref "/blog/" >}})。

## 按文档类型浏览
