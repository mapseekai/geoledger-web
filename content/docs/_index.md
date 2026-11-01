---
title: "文档中心"
description: "GeoLedger 官方技术文档：涵盖入门教程、任务操作指南、API 与配置参考、系统架构解析及生产运维手册。"
weight: 10
lastmod: 2026-11-01
type: docs
icon: fa-solid fa-book-open
sidebar_root_for: self
sidebar_root_link_self: true
cascade:
  type: docs
  footer_style: slim
  reading_time: false
---

欢迎来到 **GeoLedger** 文档中心。GeoLedger 为空间要素（GeoJSON Feature）提供类似 Git 的版本控制与协作工作流：通过**工作区**（Workspace）隔离未发布的草稿修改，经过**差异审阅**（Diff）与**三方合并**（Three-Way Merge）后，在单个数据库事务内原子发布为项目级**共享修订（Revision）**。

## 快速导航：按目标选择入口

| 你的目标 | 推荐阅读路径 |
|---|---|
| **首次体验与上手** | 1. [认识 GeoLedger]({{< relref "/docs/start/introduction/" >}})：花 5 分钟理解项目、数据集、工作区与修订的关系<br>2. [快速开始]({{< relref "/docs/start/quickstart/" >}})：使用 Docker Compose 启动服务并登录 Web 控制台<br>3. [完成第一次发布]({{< relref "/docs/start/first-publication/" >}})：亲手体验要素保存、差异审阅、发布与撤销 |
| **应用与脚本集成** | 1. [Python SDK 入门教程]({{< relref "/docs/start/sdk/" >}})：编写脚本完成草稿保存、发布与指定修订读取<br>2. [SDK 接入与类型参考]({{< relref "/docs/reference/sdk/" >}})：查阅 Rust、Go、TypeScript、Python 四语言客户端约定<br>3. [HTTP 业务 API]({{< relref "/docs/reference/http/" >}}) · [CLI 参考]({{< relref "/docs/reference/cli/" >}}) · [分页与一致性]({{< relref "/docs/reference/pagination/" >}}) |
| **日常数据编辑与协作** | - [Web 控制台导览]({{< relref "/docs/guides/console/" >}})：使用地图工作台、属性表与版本图<br>- [工作区编辑与冲突处理]({{< relref "/docs/guides/workspaces/" >}})：分批保存、三方合并冲突裁决与变基（Rebase）<br>- [大规模要素批量导入]({{< relref "/docs/guides/batch-ingestion/" >}}) · [纳管已有 PostGIS 表]({{< relref "/docs/guides/postgis/" >}}) · [版本化字段增删]({{< relref "/docs/guides/schema/" >}}) · [历史查询与撤销]({{< relref "/docs/guides/history/" >}}) |
| **生产部署与日常运维** | - [部署与运行指南]({{< relref "/docs/operations/deployment/" >}})：容器化部署、二进制运行、PostGIS 与反向代理配置<br>- [身份、权限与传输安全]({{< relref "/docs/operations/security/" >}})：RBAC 角色、API Key 轮换、TLS/mTLS 与数据库加密连接<br>- [备份、导出与恢复]({{< relref "/docs/operations/backup/" >}}) · [故障诊断手册]({{< relref "/docs/operations/troubleshooting/" >}}) · [配置参数参考]({{< relref "/docs/reference/configuration/" >}}) · [性能与容量规划]({{< relref "/docs/reference/performance/" >}}) |

## 文档结构说明

本站遵循现代技术文档的 [Diátaxis](https://diataxis.fr/) 规范，将内容划分为四个互补的模块：

- **入门教程（Tutorials）**：面向初次接触 GeoLedger 的读者，提供从零开始、可一步步跟随执行的完整学习闭环。
- **操作指南**（How-to Guides）与**运维指南（Operations）**：面向具体业务或运维场景（如纳管存量 PostGIS 表、增删字段、恢复中断的发布、执行备份演练），提供标准操作步骤与检查清单。
- **技术参考（Reference）**：准确定义 HTTP 接口、四语言 SDK、CLI 命令、游标分页契约、环境变量默认值以及版本兼容性边界。
- **概念与架构（Architecture & Explanation）**：深入阐述 GeoLedger 的内部机制、版本可见性模型、三方合并规则、空间存储表结构以及单事务一致性保证。

> **版本基线提示**：当前文档基于 GeoLedger 源码版本 `0.3.0-alpha.8`（提交 `9d31fb5`，存储格式版本 `19`）编写与核对。在生产或测试环境中执行操作前，建议先阅读[版本、兼容性与验证范围]({{< relref "/docs/reference/compatibility/" >}})。已发布版本说明与主分支工程演进记录请参阅[项目动态（Blog）]({{< relref "/blog/" >}})。

## 按章节浏览
