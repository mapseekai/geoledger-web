---
title: "故障诊断与常见问题排查"
linkTitle: "故障诊断"
description: "按容器启动失败、控制台登录报错、401/404 权限问题、409 版本冲突、request_id 幂等错误及 413/429/504 资源限制快速定位并解决问题。"
weight: 40
lastmod: 2026-11-01
---

当你在部署、登录或调用 API 时遇到异常，建议先记录以下四个关键信息，再对照下文对应的故障分支进行排查：

1. **响应中的 `request_id` 与业务错误码 `code`**：服务端会在每个错误响应体和 `x-request-id` 响应头中返回唯一请求 ID，可用它在服务端 JSON 日志中精准检索上下文。
2. **服务端版本与存储后端**：通过 `GET /health` 或启动日志确认当前运行版本与 `GL_STORAGE`（`sqlite` 或 `postgis`）。
3. **日志脱敏原则**：向团队或社区提交日志片段前，请务必隐去 `GL_API_KEY`、`GL_WEB_SESSION_SECRET` 与数据库连接口令。

---

## 1. 容器无法启动或 `GET /ready` 返回失败

### 典型症状
- 执行 `docker compose up` 时容器退出，或请求 `http://127.0.0.1:7881/ready` 返回 `503 Service Unavailable` / 连接被拒绝。

### 排查步骤
1. 在源码根目录运行 `docker compose ps` 和 `docker compose logs geoledger`。
2. 若使用 `--build` 首次启动，确认镜像编译是否已经完成。
3. 查看日志中的具体启动错误：
   - 是否未设置 `GL_WEB_SESSION_SECRET`（要求至少 32 字符）？
   - 数据目录 `/data`（或 `GL_DATA_DIR`）是否挂载了旧版本遗留的低格式数据库（当前要求存储格式 `19`）？
   - **SpatiaLite 扩展无法加载**：本机使用 SQLite 时，若日志包含 `cannot load SpatiaLite`，请安装可加载的 `mod_spatialite` 扩展及其依赖；Debian / Ubuntu 可使用 `libsqlite3-mod-spatialite` 包。默认加载 `mod_spatialite`，也可将 `GL_SPATIALITE_EXTENSION` 设为本机可信扩展的实际路径，例如 Linux x86-64 的 `/usr/lib/x86_64-linux-gnu/mod_spatialite.so` 或 Apple Silicon Homebrew 的 `/opt/homebrew/lib/mod_spatialite.dylib`；路径随平台和安装方式变化。
   - 本机端口 `7881`（HTTP）、`7882`（gRPC）或 `3000`（Web）已被其他进程占用？

### 解决方案
- 补齐缺失的环境变量（参见 **[配置参数参考]({{< relref "/docs/reference/configuration/" >}})**）。
- 若因复用旧版本数据卷导致存储格式不匹配，请为当前版本指定全新的数据目录或空数据库卷（旧库请使用匹配的旧版二进制读取或导出，切勿手动篡改数据库中的格式版本号）。

---

## 2. Web 控制台页面能打开，但无法登录或首次改密失败

### 典型症状
- 浏览器可以加载登录界面，但提交用户名密码后报错，或登录后立即跳回登录页。

### 排查步骤
1. **核对访问地址与 `GL_WEB_ORIGIN`**：检查浏览器地址栏实际使用的协议、域名和端口是否与 `GL_WEB_ORIGIN` 完全一致。请注意：**`http://localhost:3000` 与 `http://127.0.0.1:3000` 在浏览器安全策略中属于不同的 Origin**！
2. **核对 BFF 后端连通性**：确认 `GL_WEB_ENDPOINT` 指向的 `geoledger-server` HTTP 地址（默认 `http://127.0.0.1:7881`）已通过 `/ready` 检查。
3. **核对初始凭据**：首次启动未指定密码时，确认读取的是当前数据目录下的 `/data/initial-admin-*.json`，且账号未被停用。

### 解决方案
- 统一使用 `GL_WEB_ORIGIN` 配置的完整地址（如 `http://localhost:3000`）访问控制台，并按 **[快速开始]({{< relref "/docs/start/quickstart/" >}})** 完成首次强制改密。

---

## 3. 调用接口返回 `401 Unauthenticated` 或已知资源返回 `404 Not Found`

### 典型症状
- SDK / CLI / HTTP 请求返回 `401`，或者访问确定存在的项目 / 工作区时返回 `404`。

### 排查步骤
1. **为什么已知资源会返回 `404`？**
   为了防止未授权用户枚举私有项目或他人工作区，当调用者**不是目标项目的有效成员**，或尝试操作**属于其他用户的工作区**时，服务端会统一按资源不可见（`404`）处理。
2. **检查凭据与用户状态**：
   - API Key 是否已过期、被撤销，或用户在创建该 Key 后修改过密码（改密会自动撤销该用户先前的会话与 Key）？
   - 用户的项目角色是否已被移除？

### 解决方案
- 由管理员或项目 `owner` 在控制台核实用户状态与项目成员列表（参见 **[身份与权限]({{< relref "/docs/operations/security/" >}})**），使用有效的个人 API Key 重新连接。若此时手头有未确认的发布请求（`pending_publication`），恢复权限后继续使用原意图确认即可。

---

## 4. 保存或发布时返回 `409 Conflict`

### 典型症状
- 调用 `save`、`resolve`、`rebase` 或 `publish` 时收到 `409 Conflict`。

### 排查与解决（按具体冲突原因区分）

| 409 细分场景 | 原因说明 | 正确处理步骤 |
|---|---|---|
| **工作区版本不匹配（`workspace version mismatch`）** | 本地持有的 `expected_workspace_version` 落后于服务端工作区的最新 `version` | 调用 `get_workspace` / `refresh` 刷新工作区状态，检查是否有其他终端已写入草稿，确认后再提交 |
| **存在合并冲突或 `stale_resolution`** | 共享 `HEAD` 已推进且存在同一字段/几何冲突，或先前的冲突裁决因上下文变化而失效 | 调用 `conflicts` 分页读取最新的 `base` / `current` / `draft`，提交完整裁决结果（`resolve`）并执行 `rebase`（切勿仅修改版本号强行覆盖） |
| **业务源表发生漂移** | 返回 `business table changed outside GeoLedger; reconcile the source before publishing`。可能是源表结构或保护触发器发生变化，也可能检测到绕过 GeoLedger 的写入 | 暂停受影响的写入，保留完整数据库备份与变更证据，由 DBA 核对源表和触发器；在隔离环境验证[备份恢复]({{< relref "/docs/operations/backup/" >}})方案，并评估备份之后的数据。不要直接清空 `gl_source_changes` 或删除数据集来消除报错：删除数据集会清理相关版本历史，参见 [PostGIS 表纳管]({{< relref "/docs/guides/postgis/" >}}) |
| **字段变更基线失效（Schema 意图冲突）** | 工作区包含 `schema_edits`，但期间项目 `HEAD` 已被其他提交推进 | 先传空数组 `schema_edits: []` 撤销旧字段意图，执行 `rebase` 并读取最新 `schema` 后重新声明字段变更（见[字段增删指南]({{< relref "/docs/guides/schema/" >}})） |
| **项目已归档或工作区已关闭** | 目标项目处于 `archived`（只读）状态，或工作区已 `published` / `discarded` | 归档项目需由 `owner` 恢复后才可写入；已发布的工作区不可再次修改，请创建新工作区 |

---

## 5. 重试发布时返回 `request_id payload mismatch`

### 典型症状
- 在重试一次结果未知的 `publish` 请求时，收到 `409 Conflict: request_id payload mismatch`。

### 原因与解决方案
- **原因**：客户端复用了上一次发布的 `request_id`（UUID），但修改了请求中的 `expected_workspace_version` 或发布说明 `message`。
- **解决**：找回首次发起发布时的完整原始请求和身份，使用原负载重试。若回执存在且调用者仍有读取权限，服务端会返回原回执；否则应根据响应继续排查（详见 **[发布结果恢复]({{< relref "/docs/guides/publication-recovery/" >}})**）。

---

## 6. 请求返回 `413 Payload Too Large`、`429 Too Many Requests` 或 `504 Gateway Timeout`

### 典型症状
- 大批量保存、大范围查询或高并发压测时触发资源保护状态码。

### 原因与调优方案
- **`413 Payload Too Large`**：单次请求体或单页查询编码响应超出了字节预算（`GL_MAX_REQUEST_BYTES` / `GL_MAX_RESPONSE_BYTES`，默认各 64 MiB）。请减小单页查询的 `limit`（默认 100，最大 1,000）或分批保存的批次大小，复杂大切片几何也可适当调大服务端预算参数。
- **`429 Too Many Requests`**：并发执行槽（`GL_MAX_CONCURRENCY`，默认 20）或并发收发内存池（默认各 256 MiB）已满，或触发了 IP / 身份速率限制。请根据响应头 `Retry-After: 1` 控制客户端并发度，避免无退避的死循环重试。
- **`504 Gateway Timeout`（或 `deadline_exceeded`）**：单次操作耗时超过了 `GL_REQUEST_TIMEOUT_SECS`（默认 30 秒）或数据库语句/锁等待期限。
  - 若发生在查询阶段：检查 PostGIS 纳管大表是否已创建 `GiST` 空间索引，并缩小查询 `bbox` 或 `limit`。
  - **若发生在 `publish` 阶段**：数据库事务可能在超时瞬间恰好提交成功！**请务必按 [发布结果恢复]({{< relref "/docs/guides/publication-recovery/" >}}) 流程使用原 `request_id` 确认结果**。

---

## 7. PostGIS 数据库连接或表纳管失败

### 典型症状
- 设置 `GL_STORAGE=postgis` 后服务拒绝启动，或调用 `register_table` 时被拒绝。

### 排查与解决方案
1. **连接与 TLS 校验失败**：当配置为 `postgis` 时，GeoLedger 绝不会静默回退到 SQLite。检查 `GL_DATABASE_URL` 的证书路径（`sslrootcert`）、主机名是否匹配证书 SAN，以及 PostgreSQL 是否已启用 `postgis` 扩展。
2. **存量表注册被拒绝**：核对操作者是否同时具备平台管理员与项目写权限；核对源表是否为无 RLS、重写规则和继承的持久独立普通表，是否具备单列主键、明确子类型的 `geometry` 列与有限数值坐标，以及服务数据库账号是否拥有该表的所有者权限以创建保护触发器（详见 **[PostGIS 表纳管指南]({{< relref "/docs/guides/postgis/" >}})**）。

## 实现依据

- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/server/src/main.rs)
- [crates/spatialite/src/lib.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/spatialite/src/lib.rs) · [crates/engine/src/session.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/session.rs)
- [crates/engine/src/session/tables.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/session/tables.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/workspace.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/publication.rs)
- [docs/security.md](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/docs/security.md)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/docs/production.md)
