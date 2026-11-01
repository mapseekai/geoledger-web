---
title: "配置身份、RBAC 权限与传输安全"
linkTitle: "身份与权限"
description: "管理平台用户与密码生命周期、分配项目级 RBAC 角色、轮换个人 API Key，并配置控制台会话与全链路 TLS 加密。"
weight: 20
lastmod: 2026-10-29
---

GeoLedger 采用清晰的分层安全模型：**用户身份**（Subject UUID）由数据库全局管理，**业务数据访问权限**由项目级角色（RBAC）控制，而**浏览器控制台**与**程序客户端**（SDK / CLI / HTTP）分别使用独立的会话与凭据机制，所有请求最终由同一个业务应用层（`Application`）强制执行授权检查。

## 1. 用户身份与项目级 RBAC 角色

### 初始管理员与用户生命周期

- **初始管理员引导**：首次启动未设置 `GL_ADMIN_PASSWORD` 时，系统自动创建 `admin` 账号（可通过 `GL_ADMIN_USERNAME` 自定义）并将随机初始密码写入私有文件 `initial-admin-<id>.json`。首次登录或被管理员重置密码后，用户必须先完成密码修改才能访问业务功能。
- **稳定 UUID 身份**：每个用户在数据库中拥有不可变的 UUID（即协议中的 `subject`）。用户名（3–64 位 ASCII 小写字母、数字、`.`、`_`、`-`）后续修改不会影响其已有的项目成员身份、工作区归属或历史审计记录。
- **密码存储与限速保护**：密码使用随机盐 **Argon2id**（19 MiB 内存、2 次迭代）哈希存储，并在有并发上限的独立阻塞线程池中校验，避免占用数据库事务锁；登录接口内置按用户名和来源 IP 的令牌桶限流，并对不存在的账号执行等耗时虚拟校验以防止枚举。

### 项目成员角色（RBAC）与平台管理员边界

项目创建者自动成为该项目的 `owner`。`owner` 可在控制台“访问权限”页面或通过 `set_member` 接口按用户 UUID 为团队成员分配以下三种角色（每个项目必须至少保留一名有效 `owner`）：

| 项目角色 | 空间数据与工作区能力 | 项目治理与审计能力 |
|---|---|---|
| **`viewer`** | 只读浏览共享要素数据、字段定义（Schema）、版本历史与提交明细 | 可按成员规则主动退出项目；不可创建工作区或修改数据 |
| **`editor`** | 具备 `viewer` 全部能力；可创建数据集、在个人工作区中保存草稿、解决冲突并发布修订 | 不可管理其他成员权限、不可归档/删除项目、不可读取项目审计日志 |
| **`owner`** | 具备 `editor` 全部能力；可读取项目级完整审计日志（`audit`） | 管理项目成员与角色、重命名项目、归档/恢复项目（只读）以及确认删除项目 |

> **重要：平台管理员（`platform_admin`）的权限边界**
> 平台管理员用于企业级账号治理（创建/停用/软删除用户、重置密码、在人员离职交接时调整任意项目的成员角色或清理孤儿项目，以及执行 PostGIS 存量表纳管）。**但平台管理员标志本身并不自动赋予读取任意项目要素、历史或审计日志的数据权限**——要查看或编辑具体项目的数据，仍须作为该项目的显式成员。

## 2. 个人 API Key 的创建、使用与平滑轮换

CLI、四语言 SDK 以及外部 HTTP 业务集成均使用以 `glk_` 开头（后接 32 字节随机数十六进制编码）的**个人 API Key** 进行认证：

1. **仅展示一次明文**：在控制台 **API Key** 页面创建密钥时，数据库仅存储其 SHA-256 摘要，明文仅在创建成功时展示一次。
2. **权限继承与强一致失效**：API Key 严格继承所属用户的项目 RBAC 角色，不会获得额外特权。当密钥被撤销、删除、到期，或者所属用户被禁用、软删除或修改了密码时，该密钥在**下一次请求时立即失效**。
3. **零停机轮换流程**：
   - 每个用户可同时持有多个有效 API Key（建议为不同脚本或服务分配独立命名的 Key 并设置合理的到期时间）。
   - 轮换时，先创建一枚新 Key，更新客户端配置并验证读写正常后，再在控制台撤销并删除旧 Key。
4. **安全的本地文件存储**：使用 CLI 时，请将 Key 存入权限为 `0600` 的普通文件并通过 `--api-key-file`（或 `GL_API_KEY_FILE`）读取，切勿将 Key 放入 URL 查询参数或公开可读的脚本中（Unix 下 CLI 会自动拒绝符号链接或组/其他人可读的凭据文件）。

## 3. Web 控制台会话（Session）安全

浏览器控制台不直接使用长期 API Key，而是通过 Next.js BFF 与数据库协同维护有状态会话：

- **加密不透明 Cookie**：浏览器仅保存经 `GL_WEB_SESSION_SECRET` 加密的 `HttpOnly`、`SameSite=Strict`（HTTPS 下启用 `Secure`）Cookie，最长有效期 8 小时。
- **服务端双重时效管理**：数据库记录会话摘要与活跃时间，默认**空闲超时为 30 分钟**、**绝对寿命上限为 12 小时**。用户点击退出登录、修改密码或被管理员停用时，数据库会话立即撤销。
- **敏感操作二次验证**：在控制台中修改用户状态、管理他人密钥或变更项目成员权限等敏感治理操作，系统会独立要求再次验证当前用户的登录密码。

## 4. 全链路传输加密（TLS / mTLS）

在生产环境中，建议为客户端到服务端、以及服务端到 PostgreSQL 数据库配置全链路 TLS 加密：

### 服务端 HTTP 与 gRPC TLS / mTLS

- **网关终结或原生 TLS**：你既可以在可信 Nginx / Caddy 网关上终结 TLS，也可以直接为 `geoledger-server` 配置 `GL_TLS_CERT`（PEM 证书链）与 `GL_TLS_KEY`（PEM 私钥），让 HTTP（`h2` / `http/1.1`）和 gRPC（`h2`）监听器原生启用 TLS 1.2/1.3。
- **热重载证书**：服务端默认每 10 秒（`GL_RELOAD_INTERVAL_SECS`）自动检测证书文件更新，也可发送 `kill -HUP` 立即触发无损重载。
- **双向认证（mTLS）**：配置 `GL_TLS_CLIENT_CA` 后，服务端会强制校验客户端证书。
- **客户端默认拒绝远程明文**：四语言 SDK 与 `gl` CLI 默认仅允许对本机回环地址（`127.0.0.1`、`::1`、`localhost`）使用 `http://` 明文；连接远程地址时默认要求 `https://` 并校验证书（私有 CA 配置方式见 **[SDK 参考]({{< relref "/docs/reference/sdk/" >}})**）。

### PostgreSQL 数据库连接 TLS

`GL_DATABASE_URL` 默认采用最严格的 **`sslmode=verify-full`**，同时校验证书链与数据库主机名（拒绝 `prefer` 或 `allow` 等可能静默降级为明文的模式）：

```text
postgresql://geoledger_app@db.internal:5432/geoledger?sslmode=verify-full&sslrootcert=/etc/geoledger/db-ca.pem
```

如果还需要数据库客户端证书认证，可在连接串中追加 `sslcert` 与 `sslkey`（PKCS#8 PEM）。

## 安全验收与备份恢复提醒

- **上线前权限回归**：分别使用 `viewer`、`editor`、`owner` 与平台管理员身份测试允许的操作与越权操作，并验证撤销 API Key 及退出登录后旧凭据立即失效。
- **旧备份恢复后的凭据核查**：完整的数据库物理备份（如 SQLite `backup` 或 PostgreSQL `pg_dump`）包含备份时刻的用户、Session 与 API Key 摘要。**如果从历史备份恢复了数据库，曾经在备份时间点之后撤销的 API Key 或已离职用户的状态可能会随旧备份一同恢复**——因此在恢复实例对外开放网络访问前，务必先核查用户列表并轮换或撤销相关密钥。

## 实现依据

- [crates/engine/src/authentication.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/engine/src/authentication.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/engine/src/workspace.rs)
- [docs/security.md](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/docs/security.md)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/docs/production.md)
