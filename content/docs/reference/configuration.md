---
title: "配置参考"
linkTitle: "配置参数"
description: "查阅服务端、控制台、CLI 和验证环境的配置键、默认值与使用边界。"
weight: 40
lastmod: 2026-10-29
---

本页按固定源码的服务端参数、CLI 和环境模板列出配置。服务端参数可通过环境变量或对应 CLI 选项设置；`GL_ADMIN_PASSWORD` 仅从环境读取。Compose、服务进程和 Web 的环境需分别传入。

## 存储与数据库

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| GL_STORAGE | sqlite | sqlite 或 postgis 后端 |
| GL_DATA_DIR | ./geoledger-data | 服务数据目录 |
| GL_DATABASE_URL | 未设置 | PostGIS 连接字符串，使用该后端时必需 |
| GL_DATABASE_ALLOW_PLAINTEXT | false | 显式允许非回环数据库使用 sslmode=disable |
| GL_DB_POOL_SIZE | 20 | PostGIS 连接池容量 |
| GL_DB_STATEMENT_TIMEOUT_SECS | 30 | 数据库语句期限，秒 |
| GL_DB_LOCK_TIMEOUT_SECS | 10 | 数据库锁等待期限，秒 |
| GL_SPATIALITE_EXTENSION | 平台默认发现 | 可信 SpatiaLite 原生扩展路径 |

PostGIS 连接默认验证证书与主机名。私有 CA 通过连接参数 `sslrootcert` 指定；配置错误不会回退到 SQLite。

## 监听与 TLS

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| GL_HTTP_LISTEN | 127.0.0.1:7881 | HTTP 监听 |
| GL_GRPC_LISTEN | 127.0.0.1:7882 | gRPC 监听 |
| GL_TLS_CERT | 未设置 | 服务端 PEM 证书链，与私钥配套 |
| GL_TLS_KEY | 未设置 | 服务端 PEM 私钥 |
| GL_TLS_CLIENT_CA | 未设置 | 配置后要求客户端证书 |
| GL_HEALTH_LISTEN | 未设置 | 仅提供 health/ready 的可选明文探针监听 |
| GL_RELOAD_INTERVAL_SECS | 10 | TLS 文件检查间隔，秒；SIGHUP 可立即触发重载 |

回环监听只适合本机或容器内明确安排的代理访问。对外访问的网关与 origin 见[部署指南]({{< relref "/docs/operations/deployment/" >}})。

## 身份与平台策略

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| GL_ADMIN_USERNAME | admin | 首次初始化管理员名 |
| GL_ADMIN_PASSWORD | 未设置时随机生成 | 首次初始化密码，不重置已有账号 |
| GL_PROJECT_CREATION | anyone | anyone 或 admins，控制项目创建 |
| GL_MAX_PROJECTS_PER_SUBJECT | 0 | 普通用户拥有的项目上限；0 为不限 |

初始随机密码写入私有 `initial-admin-<id>.json`。权限与凭据生命周期见[身份与安全指南]({{< relref "/docs/operations/security/" >}})。

## 资源预算、速率与停机

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| GL_MAX_CONCURRENCY | 20 | HTTP 与 gRPC 的并行业务操作上限 |
| GL_REQUEST_TIMEOUT_SECS | 30 | 单业务请求总期限，秒 |
| GL_MAX_REQUEST_BYTES | 67108864 | 单请求编码预算，64 MiB |
| GL_MAX_RESPONSE_BYTES | 67108864 | 单响应编码预算，64 MiB |
| GL_REQUEST_MEMORY_BYTES | 268435456 | 并发接收的编码预留，256 MiB |
| GL_RESPONSE_MEMORY_BYTES | 268435456 | 并发响应的编码预留，256 MiB |
| GL_RATE_LIMIT_SUBJECT_RPS | 0 | 每个身份的持续速率；0 禁用 |
| GL_RATE_LIMIT_SUBJECT_BURST | 50 | 身份速率突发容量 |
| GL_RATE_LIMIT_IP_RPS | 0 | 鉴权前的 IP 持续速率；0 禁用 |
| GL_RATE_LIMIT_IP_BURST | 100 | IP 速率突发容量 |
| GL_TRUST_FORWARDED_FOR | false | 信任网关设置的最右侧 X-Forwarded-For |
| GL_SHUTDOWN_DRAIN_SECS | 0 | ready 转为 503 后继续服务的排空时间，秒 |
| GL_SHUTDOWN_TIMEOUT_SECS | 30 | 监听关闭后等待在途请求的时间，秒 |
| GL_DATA_TIMEOUT_SECS | 3600 | 数据管理命令期限，秒 |
| RUST_LOG | geoledger_server=info,geoledger_engine=info | JSON 日志过滤级别 |

编码预算之外仍存在 JSON 树与原生分配开销。上述值是保护参数，不构成吞吐量或总进程内存承诺。

## 控制台

| 环境变量 | 模板值 | 用途 |
|---|---|---|
| GL_WEB_ENDPOINT | http://127.0.0.1:7881 | BFF 访问的私有业务服务地址 |
| GL_WEB_ORIGIN | http://localhost:3000 | 浏览器实际访问的完整 origin |
| GL_WEB_SESSION_SECRET | 无可用默认值 | 至少 32 字符的随机 Cookie 加密密钥 |
| GL_WEB_BASEMAP_URL | 未设置 | 可选在线 XYZ 栅格底图 |
| GL_WEB_BASEMAP_ATTRIBUTION | 未设置 | 与在线底图配套的来源说明 |

`localhost` 与 `127.0.0.1` 是不同 origin。会话密钥在重启间复用并私下保管。未配置在线底图时保留离线空白底图和对应 CSP。

## CLI 与 SDK

| 环境变量 | 默认值或要求 | 用途 |
|---|---|---|
| GL_ENDPOINT | CLI 默认 http://127.0.0.1:7882 | 示例或 CLI 的 gRPC 目标；SDK 构造时显式传入 |
| GL_API_KEY | 未设置 | 个人 API Key |
| GL_API_KEY_FILE | 未设置 | CLI 或示例读取的私有纯文本文件 |
| GL_CA_FILE | 未设置 | CLI 的私有 CA PEM 文件 |
| GL_ALLOW_INSECURE_TRANSPORT | false | 显式允许非回环 SDK / CLI 明文连接 |

CLI 凭据的互斥规则见 [CLI 参考]({{< relref "/docs/reference/cli/" >}})。各 SDK 的 CA 与明文选项见 [SDK 参考]({{< relref "/docs/reference/sdk/" >}})。

## 测试与部署模板专用值

| 变量 | 使用位置 | 用途 |
|---|---|---|
| GL_TEST_DATABASE_URL | 可选 PostGIS 测试 | 一次性测试数据库 |
| GL_DRILL_DATABASE_URL | 备份演练脚本 | 用于逻辑导入的空 PostGIS 数据库 |
| GL_DB_PASSWORD | Compose 生产模板 | 数据库初始化角色密码 |
| GL_DB_APP_PASSWORD | Compose 生产模板 | 受限运行角色密码 |

这些变量不代表普通业务请求参数。初始化脚本只作用于新卷；已有数据库的角色和授权由 DBA 单独配置。

## 实现依据

- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/main.rs)
- [.env.example](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/.env.example)
- [web/.env.example](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/web/.env.example)
- [crates/cli/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/cli/src/main.rs)
- [deploy/compose.production.yaml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/deploy/compose.production.yaml)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
