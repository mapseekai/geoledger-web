---
title: "运维指南"
description: "面向系统管理员与 SRE 的生产部署、身份与传输安全、数据库备份恢复及故障排查指南。"
weight: 50
lastmod: 2026-10-29
icon: fa-solid fa-server
cascade:
  doc_type: howto
  ui:
    section_index: list
---

本章节面向负责 GeoLedger 服务部署、数据库维护与安全治理的系统管理员与运维工程师。在将 GeoLedger 投入生产环境前，建议先在隔离的预发布环境中验证存储格式兼容性、最小权限角色、TLS 证书链以及备份恢复演练。

## 运维主题导航

- **[部署与运行]({{< relref "/docs/operations/deployment/" >}})**：对比统一容器、原生二进制（systemd）与 PostGIS + TLS 网关生产架构，配置健康检查探针、Prometheus 监控指标与优雅停机排空。
- **[身份、权限与传输安全]({{< relref "/docs/operations/security/" >}})**：配置初始管理员、项目级 RBAC（`viewer` / `editor` / `owner`）、个人 API Key 轮换、控制台加密 Session 以及 HTTP/gRPC/PostgreSQL 的 TLS 与 mTLS。
- **[备份、导出与恢复]({{< relref "/docs/operations/backup/" >}})**：掌握 SQLite 在线备份（`backup` / `restore`）、PostgreSQL 原生全库备份，以及跨存储后端的可移植逻辑导出与校验（`export` / `import` / `verify`）。
- **[故障诊断手册]({{< relref "/docs/operations/troubleshooting/" >}})**：按容器启动、控制台登录、权限拒绝、乐观锁冲突、容量限流（`413` / `429` / `504`）与 PostGIS 纳管错误快速定位根因。

> **相关参考**：所有服务端、控制台与 CLI 环境变量的完整列表及默认值统一维护在 **[配置参数参考]({{< relref "/docs/reference/configuration/" >}})**；版本升级与存储格式（Format `19`）要求详见 **[版本与兼容性]({{< relref "/docs/reference/compatibility/" >}})**。
