---
title: "部署与生产运行指南"
linkTitle: "部署与运行"
description: "规划 GeoLedger 的容器或二进制部署形态，配置存储后端、TLS 反向代理网关、健康探针、监控指标与优雅停机。"
weight: 10
lastmod: 2026-10-29
---

在部署 GeoLedger 时，建议始终固定源码提交 SHA 或容器镜像的完整 `@sha256` 摘要（Digest），明确持久化数据目录与网络信任边界，并在正式开放用户访问前跑通“登录 → 草稿保存 → 原子发布 → 备份恢复”的完整验收链路。

## 部署形态选型

GeoLedger 支持三种主流部署方式，可根据团队规模与并发负载选择：

| 部署形态 | 适用场景 | 架构特点与准备项 |
|---|---|---|
| **1. 统一容器部署（SQLite）** | 快速评估、中小团队单机运行、轻量级写入 | 单镜像内聚 `geoledger-server`、`gl` CLI、Next.js 控制台与 SpatiaLite 依赖（以非特权 `UID 10001` 运行）；需挂载本地持久化卷 `/data` |
| **2. 原生二进制 + systemd** | 已有主机进程管理体系或定制化系统集成 | 通过 `cargo build --release --locked --bins` 编译 `geoledger-server` 与 `gl`，搭配主机 SpatiaLite 库与独立部署的 Web 控制台 |
| **3. PostGIS + TLS 网关生产栈** | 多人高并发协作、存量 PostGIS 业务表纳管、集中化数据库运维 | 参考仓库 `deploy/compose.production.yaml`：由 Nginx / Caddy 终结外部 HTTPS/gRPC TLS，后端以 `sslmode=verify-full` 连接专用 PostgreSQL + PostGIS 实例 |

> **版本与存储格式检查**：当前版本使用**存储格式 `19`**。新部署会自动将空目录或空库初始化为格式 `19`；升级前请先查阅 **[版本与兼容性]({{< relref "/docs/reference/compatibility/" >}})**，切勿将旧格式（如格式 `16` 或 `18`）的数据卷直接挂载给新版本服务。

## 步骤 1：准备持久化目录与初始身份

1. **服务端数据目录（`GL_DATA_DIR`）**：
   - **SQLite 模式**：保存数据库文件、WAL 日志及初始化凭据文件，**必须位于可靠的本地文件系统**（请勿使用不支持 POSIX 文件锁的网络挂载盘）。
   - **PostGIS 模式**：业务与身份数据保存在 PostgreSQL 中，但服务端仍需使用 `GL_DATA_DIR` 写入首次启动随机生成的私有管理员凭据文件 `initial-admin-<id>.json`（权限 `0600`）。
2. **固定控制台会话密钥（`GL_WEB_SESSION_SECRET`）**：
   - 生成至少 32 字符的高熵随机字符串（如 `openssl rand -base64 48`）并保存在秘密管理系统中，确保容器或进程重启后浏览器现有会话平滑延续。
3. **完成首次改密并清理明文文件**：
   - 首次启动后，使用 `initial-admin-<id>.json` 中的随机密码登录控制台完成强制改密，随后删除该初始化明文文件，并为自动化脚本单独创建个人 API Key（详见 **[身份与权限]({{< relref "/docs/operations/security/" >}})**）。

## 步骤 2：配置存储后端（SQLite 或 PostGIS）

- **默认 SQLite + SpatiaLite**：无需额外数据库服务，指定 `--storage sqlite --data-dir /data` 即可。
- **生产级 PostgreSQL + PostGIS**：
  1. 由 DBA 创建专用数据库并安装扩展：`CREATE EXTENSION IF NOT EXISTS postgis;`。
  2. 创建非超级用户的应用运行角色（如 `geoledger_app`），授予 `public` schema 的 `USAGE, CREATE` 权限（若需纳管存量业务表，还需授予对应表的读写与所有者权限，详见 **[PostGIS 表纳管]({{< relref "/docs/guides/postgis/" >}})**）。
  3. 配置服务端环境变量，默认启用严格的 `sslmode=verify-full` 证书与主机名校验：

```sh
export GL_STORAGE=postgis
export GL_DATABASE_URL='postgresql://geoledger_app@db.internal:5432/geoledger?sslmode=verify-full&sslrootcert=/etc/geoledger/db-ca.pem'
```

> **提示**：仓库的 `deploy/compose.production.yaml` 提供了包含 PostGIS（强制 `hostssl` + `scram-sha-256`）、只读根文件系统容器与 Nginx TLS 网关的完整生产编排模板。注意数据库初始化脚本仅在首次创建空卷时运行，已有数据库的角色与权限变更需由 DBA 执行。

## 步骤 3：配置 Web 控制台与反向代理网关

在生产环境中，建议通过反向代理网关（仓库提供 `deploy/gateway/nginx.conf` 与 `deploy/gateway/Caddyfile` 参考配置）统一对外提供 HTTPS 与 HTTP/2 gRPC 访问：

1. **区分内部 BFF 地址与外部浏览器 Origin**：
   - `GL_WEB_ENDPOINT`：Next.js BFF 在内部网络访问 `geoledger-server` HTTP 接口的私有地址（同一容器内默认为 `http://127.0.0.1:7881`）。
   - `GL_WEB_ORIGIN`：用户在浏览器地址栏实际访问的完整外部 Origin（例如 `https://console.geoledger.example`）。控制台会严格校验请求的 Origin 头以防御 CSRF，因此域名、协议或端口变更时必须同步更新 `GL_WEB_ORIGIN`。
2. **网关路由与真实客户端 IP**：
   - 将浏览器流量路由至控制台（`:3000`），将公开 HTTP API 路由至 `:7881`，将 gRPC 流量以 HTTP/2（`h2`）转发至 `:7882`，并透传 `x-request-id` 请求头。
   - 仅当服务明确部署在可信反向代理之后、且网关已正确覆写 `X-Forwarded-For` 时，才将 `GL_TRUST_FORWARDED_FOR` 设为 `true`，以便按真实客户端 IP 执行认证前限流。

## 步骤 4：健康检查、监控指标与上线验收

GeoLedger 内置了完善的探针与可观测性接口，便于接入 Kubernetes、Docker Compose 或 Prometheus：

| 运维端点 / 项 | 访问方式与认证 | 用途与验收标准 |
|---|---|---|
| `GET /health` | 无需认证（或通过 `GL_HEALTH_LISTEN` 明文端口） | **存活探针（Liveness）**：返回 `{"ok":true,"version":"..."}` |
| `GET /ready` | 无需认证（最多 2 秒超时） | **就绪探针（Readiness）**：校验服务未处于停机排空状态、具备可用执行槽，且数据库连接与存储格式（`19`）正常 |
| `gRPC Health` | 标准 `grpc.health.v1.Health`（服务名 `geoledger.v1.GeoLedger`） | gRPC 负载均衡健康检查；停机排空时自动切换为 `NOT_SERVING` |
| `GET /metrics` | 需携带有效 `Authorization: Bearer <api-key>` | 输出 Prometheus 指标（请求吞吐、延迟直方图、并发槽水位、PostGIS 连接池状态、限流与冲突计数）；配套告警规则见 `deploy/monitoring/prometheus-rules.yaml` |
| 结构化访问日志 | 标准输出单行 JSON（通过 `RUST_LOG` 控制级别） | 每次业务调用记录 `request_id`、`protocol`、`operation`、`status`、`duration_ms` 与 `subject`，便于按错误回执中的 `request_id` 精准检索日志 |

## 优雅停机与版本回退规范

- **优雅停机排空（Graceful Shutdown）**：
  当收到 `SIGTERM` 或 `Ctrl+C` 时，`geoledger-server` 会先将 `/ready` 和 gRPC 健康状态切换为 `503 / NOT_SERVING`，并保持 `GL_SHUTDOWN_DRAIN_SECS` 秒供网关摘除流量；随后关闭监听器，在 `GL_SHUTDOWN_TIMEOUT_SECS`（默认 30 秒）内等待在途数据库事务完成。请确保容器编排器的终止宽限期（`stop_grace_period`）大于这两个时间之和（建议设为 60 秒）。
- **配置与版本回退**：
  - 若停机期间客户端有正在执行的 `publish` 请求中断，服务恢复后客户端只需沿用原 `request_id` 重试即可确认结果（见 **[发布结果恢复]({{< relref "/docs/guides/publication-recovery/" >}})**）。
  - 如需回退到使用旧存储格式的历史版本程序，必须同时切回升级前独立保留的旧格式数据库备份，切勿让旧版本二进制直接读取已初始化为高格式的数据库。

## 实现依据

- [compose.yaml](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/compose.yaml)
- [Dockerfile](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/Dockerfile)
- [deploy/compose.production.yaml](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/deploy/compose.production.yaml)
- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/server/src/main.rs)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/docs/production.md)
