---
title: "技术参考"
description: "GeoLedger 权威技术契约：涵盖版本与兼容性矩阵、四语言 SDK 规范、HTTP 业务 API、CLI 命令行、游标分页与服务端配置参数。"
weight: 30
lastmod: 2026-10-29
icon: fa-solid fa-code
cascade:
  doc_type: reference
  ui:
    section_index: list
---

本章节提供 GeoLedger 协议、客户端接口与运行时配置的权威参考手册。在编写集成代码或调整生产配置时，可随时查阅以下对应规范：

## 参考目录

- **[版本、兼容性与验证范围]({{< relref "/docs/reference/compatibility/" >}})**：核对文档对应的源码提交基线（`5bf353c`）、发布标签（`v0.3.0-alpha.7`）、存储格式版本（`19`）与协议包名（`geoledger.v1`）。
- **[SDK 接入与类型参考]({{< relref "/docs/reference/sdk/" >}})**：查阅 Rust、Go、TypeScript / Node.js 与 Python 四语言客户端的安装方式、连接选项、业务方法矩阵、64 位大整数处理及工作区并发约定。
- **[HTTP 业务 API 参考]({{< relref "/docs/reference/http/" >}})**：查阅 `POST /api/v1/{operation}` 全部 30 个业务操作的职责、JSON 请求与响应契约、空值语义及 HTTP 状态码映射。
- **[CLI 命令行参考]({{< relref "/docs/reference/cli/" >}})**：查阅远程客户端 `gl` 的全局连接参数、凭据文件安全要求、快捷查询子命令与通用 `call` 调用方式。
- **[分页与一致性参考]({{< relref "/docs/reference/pagination/" >}})**：查阅 `features`、`diff`、`conflicts`、`commit`、`history` 与 `audit` 的游标（`after` / `next_after`）语义、快照固定规则与删除遮蔽机制。
- **[配置参数参考]({{< relref "/docs/reference/configuration/" >}})**：查阅服务端、Web 控制台、CLI 及生产部署模板中所有 `GL_*` 环境变量的默认值与调优边界。
- **[性能基准与容量规划参考]({{< relref "/docs/reference/performance/" >}})**：查阅历史格式 13 测试条件和结果，以及在目标环境中测量容量的方法。
