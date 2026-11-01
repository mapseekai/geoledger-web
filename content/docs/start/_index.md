---
title: "入门教程"
description: "从零开始了解 GeoLedger 的核心概念，启动本地环境，完成第一次空间要素发布与 SDK 接入。"
weight: 10
lastmod: 2026-10-29
icon: fa-solid fa-rocket
cascade:
  doc_type: tutorial
  ui:
    section_index: list
---

本章节为你提供一条循序渐进的上手路径。通过四个简短的步骤，你将掌握 GeoLedger 的核心版本模型，在本地启动完整服务，并分别通过 Web 控制台和代码 SDK 完成要素发布与历史回溯。

## 推荐学习顺序

1. **[认识 GeoLedger]({{< relref "/docs/start/introduction/" >}})**：理解项目（Project）、数据集（Dataset）、要素（Feature）、工作区（Workspace）与共享修订（Revision）之间的协作关系。
2. **[快速开始]({{< relref "/docs/start/quickstart/" >}})**：通过 Docker Compose 一键启动包含服务端、CLI 与 Web 控制台的本地测试环境，并完成初始管理员登录。
3. **[完成第一次发布]({{< relref "/docs/start/first-publication/" >}})**：在工作区中保存一条监测点要素，审阅差异并发布为共享修订，随后体验属性更新与非破坏性撤销（Restore）。
4. **[Python SDK 入门教程]({{< relref "/docs/start/sdk/" >}})**：使用官方 Python 客户端以编程方式创建工作区、提交要素、获取发布回执，并按固定修订号精确读回数据。

> **环境说明**：入门教程均使用合成演示数据，旨在帮助你快速跑通核心闭环。若需了解生产环境的持久化、TLS 网关、PostGIS 权限与备份恢复规范，请在完成入门后参阅[运维指南]({{< relref "/docs/operations/" >}})。
