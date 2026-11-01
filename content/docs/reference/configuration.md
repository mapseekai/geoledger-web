---
title: "配置参数参考（环境变量与命令行）"
linkTitle: "配置参数"
description: "查阅 geoledger-server、Web 控制台、远程 CLI（gl）以及生产部署模板的全部环境变量、命令行选项、默认值与安全边界。"
weight: 40
lastmod: 2026-11-01
---

本页汇总了 GeoLedger 服务端（`geoledger-server`）、Web 控制台、远程 CLI（`gl`）以及生产编排模板支持的全部配置项。

服务端参数既可通过环境变量注入，也可通过对应的命令行参数传入（出于安全考量，初始密码 `GL_ADMIN_PASSWORD` 仅支持通过环境变量读取，不提供命令行标志以防出现在进程列表中）。源码仓库根目录的 `.env.example` 与 `web/.env.example` 提供了完整的配置模板。

## 1. 存储引擎与数据库连接（`geoledger-server`）

| 环境变量 | 对应 CLI 参数 | 默认值 | 参数说明与约束 |
|---|---|---|---|
| `GL_STORAGE` | `--storage` | `sqlite` | 存储后端类型：可选 `sqlite`（SQLite + SpatiaLite）或 `postgis`（PostgreSQL + PostGIS） |
| `GL_DATA_DIR` | `--data-dir` | `./geoledger-data` | 服务端持久化数据目录（存放 SQLite 数据库、WAL 日志及首次启动生成的 `initial-admin-<id>.json`） |
| `GL_DATABASE_URL` | `--database-url` | 未设置 | PostGIS 模式下必填的 PostgreSQL 连接串；默认强制 `sslmode=verify-full`（可通过 `sslrootcert` 指定私有 CA） |
| `GL_DATABASE_ALLOW_PLAINTEXT` | `--database-allow-plaintext` | `false` | 是否允许在隔离内网对非回环主机使用 `sslmode=disable` 的明文数据库连接 |
| `GL_DB_POOL_SIZE` | `--db-pool-size` | `20` | PostGIS 模式下的业务数据库连接池最大容量 |
| `GL_DB_STATEMENT_TIMEOUT_SECS` | `--db-statement-timeout-secs` | `30` | PostgreSQL 单条 SQL 语句执行超时上限（秒） |
| `GL_DB_LOCK_TIMEOUT_SECS` | `--db-lock-timeout-secs` | `10` | PostgreSQL 事务锁等待超时上限（秒） |
| `GL_SPATIALITE_EXTENSION` | *(仅环境变量)* | `mod_spatialite` | SQLite 模式下管理员指定的可信 `mod_spatialite` 动态库路径（加载完成后立即关闭 SQLite 动态加载权限） |

例如，可在启动服务前设置 `export GL_SPATIALITE_EXTENSION=/path/to/mod_spatialite`，路径应指向当前主机可信的扩展库。

> **注意**：当显式设置 `GL_STORAGE=postgis` 时，若数据库连接或证书校验失败，服务端会立即报错退出，绝不会静默回退到本地 SQLite。

## 2. 网络监听与服务端 TLS / mTLS（`geoledger-server`）

| 环境变量 | 对应 CLI 参数 | 默认值 | 参数说明与约束 |
|---|---|---|---|
| `GL_HTTP_LISTEN` | `--http` | `127.0.0.1:7881` | 业务 HTTP API、服务发现与监控端点的监听地址 |
| `GL_GRPC_LISTEN` | `--grpc` | `127.0.0.1:7882` | 业务 gRPC（`geoledger.v1`）与 gRPC 健康检查的监听地址 |
| `GL_TLS_CERT` | `--tls-cert` | 未设置 | 服务端 PEM 证书链文件路径（与 `GL_TLS_KEY` 同时配置时，HTTP 与 gRPC 监听器均启用 TLS 1.2/1.3） |
| `GL_TLS_KEY` | `--tls-key` | 未设置 | 服务端 PEM 私钥文件路径（支持 PKCS#8、PKCS#1 或 SEC1） |
| `GL_TLS_CLIENT_CA` | `--tls-client-ca` | 未设置 | 客户端 CA 根证书（PEM）；配置后在 HTTP 与 gRPC 上强制启用双向认证（mTLS） |
| `GL_RELOAD_INTERVAL_SECS` | `--reload-interval-secs` | `10` | 自动检测 TLS 证书文件更新的轮询间隔（秒）；向进程发送 `SIGHUP` 可立即触发热重载 |
| `GL_HEALTH_LISTEN` | `--health-listen` | 未设置 | 可选的独立明文探针监听地址（例如 `127.0.0.1:7880`），仅暴露无认证的 `/health` 与 `/ready`，便于启用服务端 TLS 时供容器编排器探活 |

## 3. 初始身份与项目治理策略（`geoledger-server`）

| 环境变量 | 对应 CLI 参数 | 默认值 | 参数说明与约束 |
|---|---|---|---|
| `GL_ADMIN_USERNAME` | `--admin-username` | `admin` | 首次初始化空数据库时创建的平台管理员用户名 |
| `GL_ADMIN_PASSWORD` | *(仅环境变量)* | 未设置（自动随机生成） | 首次初始化管理员的密码；未设置时生成高熵随机密码并写入 `GL_DATA_DIR/initial-admin-<id>.json`（`0600`）。对已存在的账号重启不会覆盖原密码 |
| `GL_PROJECT_CREATION` | `--project-creation` | `anyone` | 控制谁可以创建新项目：`anyone`（所有有效认证用户）或 `admins`（仅平台管理员） |
| `GL_MAX_PROJECTS_PER_SUBJECT` | `--max-projects-per-subject` | `0` | 单个普通用户可同时拥有（作为有效 `owner` 且未删除）的项目数量上限；`0` 表示不限制（平台管理员不受此配额限制） |

## 4. 并发容量、内存预算、速率限制与优雅停机

| 环境变量 | 默认值 | 参数说明与调优边界 |
|---|---|---|
| `GL_MAX_CONCURRENCY` | `20` | HTTP 与 gRPC 共享的并发业务执行槽上限；超出时立即返回 `429 Too Many Requests` |
| `GL_REQUEST_TIMEOUT_SECS` | `30` | 单次业务请求（含鉴权、数据库锁等待、执行与编码）的总期限上限（秒） |
| `GL_MAX_REQUEST_BYTES` | `67108864`（64 MiB） | 单个请求体的最大编码字节数上限；超出时返回 `413 Payload Too Large` |
| `GL_MAX_RESPONSE_BYTES` | `67108864`（64 MiB） | 单个响应体的最大编码字节数上限；超出时提示减小分页 `limit` |
| `GL_REQUEST_MEMORY_BYTES` | `268435456`（256 MiB） | 所有并发正在接收请求共享的编码字节预留池上限 |
| `GL_RESPONSE_MEMORY_BYTES` | `268435456`（256 MiB） | 所有并发正在生成与发送响应共享的编码字节预留池上限 |
| `GL_RATE_LIMIT_SUBJECT_RPS` | `0` | 每个已认证用户（`subject` UUID）的持续每秒请求速率限制；`0` 表示禁用 |
| `GL_RATE_LIMIT_SUBJECT_BURST` | `50` | 每个已认证用户的令牌桶突发容量（当 `GL_RATE_LIMIT_SUBJECT_RPS > 0` 时生效） |
| `GL_RATE_LIMIT_IP_RPS` | `0` | 鉴权前按客户端 IP 执行的持续每秒请求速率限制；`0` 表示禁用 |
| `GL_RATE_LIMIT_IP_BURST` | `100` | 客户端 IP 令牌桶突发容量（当 `GL_RATE_LIMIT_IP_RPS > 0` 时生效） |
| `GL_TRUST_FORWARDED_FOR` | `false` | 是否信任反向代理传入的 `X-Forwarded-For` 最右侧地址作为客户端 IP（**仅在受控可信网关后开启**） |
| `GL_SHUTDOWN_DRAIN_SECS` | `0` | 收到停止信号后，先将 `/ready` 设为 `503` 并继续接收流量以供负载均衡摘流的排空等待秒数 |
| `GL_SHUTDOWN_TIMEOUT_SECS` | `30` | 关闭网络监听后，等待在途数据库事务执行完毕的最大超时秒数 |
| `GL_DATA_TIMEOUT_SECS` | `3600` | `backup`、`restore`、`export`、`import`、`verify` 本地数据管理命令的执行超时上限（秒） |
| `RUST_LOG` | `geoledger_server=info,geoledger_engine=info` | 结构化 JSON 日志的模块过滤级别（支持 `debug`、`info`、`warn`、`error`） |

> **容量规划提示**：`GL_REQUEST_MEMORY_BYTES` 与 `GL_RESPONSE_MEMORY_BYTES` 管控的是传输层与查询批次的 UTF-8 / Protobuf 编码字节预留额度；进程运行时的 JSON 语法树、原生几何对象与数据库连接驱动还会产生额外内存开销，请结合主机实际物理内存规划容器限额。

## 5. Web 控制台配置（`web/.env.local` 或容器环境）

| 环境变量 | 默认模板值 | 参数说明与约束 |
|---|---|---|
| `GL_WEB_ENDPOINT` | `http://127.0.0.1:7881` | Next.js BFF 服务端在内部网络调用 `geoledger-server` HTTP 接口的地址 |
| `GL_WEB_ORIGIN` | `http://localhost:3000` | 用户在浏览器中访问控制台的完整外部 Origin（如 `https://console.geoledger.example`）；用于严格的同源与 CSRF 校验 |
| `GL_WEB_SESSION_SECRET` | **必填（无默认值）** | 至少 32 字符的高熵随机密钥（可用 `openssl rand -base64 48` 生成），用于加密浏览器 `HttpOnly` 会话 Cookie |
| `GL_WEB_BASEMAP_URL` | 未设置 | 可选的在线 XYZ 栅格瓦片底图 URL 模板（未设置时默认使用完全离线的浅色/深色纯色底图与严格的离线 CSP） |
| `GL_WEB_BASEMAP_ATTRIBUTION` | 未设置 | 启用在线底图时在地图右下角展示的数据来源署名信息 |

## 6. 远程 CLI（`gl`）、SDK 与生产模板辅助变量

| 环境变量 | 适用范围 | 默认值 / 说明 |
|---|---|---|
| `GL_ENDPOINT` | `gl` CLI 与 SDK 示例 | `gl` 默认 `http://127.0.0.1:7882`；指定远程 gRPC 服务端地址 |
| `GL_API_KEY` | `gl` CLI 与 SDK 示例 | 个人 API Key 明文（在 CLI 中与 `GL_API_KEY_FILE` 严格互斥） |
| `GL_API_KEY_FILE` | `gl` CLI 与 SDK 示例 | 存放个人 API Key 的私有普通文件路径（Unix 下要求权限 `0600`） |
| `GL_CA_FILE` | `gl` CLI | 连接私有 CA 签发的 `https://` gRPC 服务时使用的 PEM 根证书路径 |
| `GL_ALLOW_INSECURE_TRANSPORT` | `gl` CLI 与四语言 SDK | 默认 `false`；设为 `true` 时允许对非回环地址使用明文 `http://` |
| `GL_DB_PASSWORD` | `deploy/compose.production.yaml` | 生产 Compose 模板首次初始化 PostGIS 容器时的数据库管理角色密码 |
| `GL_DB_APP_PASSWORD` | `deploy/compose.production.yaml` | 生产 Compose 模板中 `geoledger_app` 受限业务运行角色的密码 |
| `GL_TEST_DATABASE_URL` | 仓库回归测试脚本 | 运行可选 PostGIS 集成测试时指向的隔离测试库连接串 |
| `GL_DRILL_DATABASE_URL` | `scripts/backup-drill.sh` | 备份恢复演练脚本用于验证跨后端 `import` 的空 PostGIS 数据库连接串 |

## 实现依据

- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/server/src/main.rs)
- [.env.example](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/.env.example)
- [web/.env.example](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/web/.env.example)
- [crates/cli/src/main.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/cli/src/main.rs)
- [deploy/compose.production.yaml](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/deploy/compose.production.yaml)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/docs/production.md)
