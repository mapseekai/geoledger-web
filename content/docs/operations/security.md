---
title: "配置身份、权限与传输安全"
linkTitle: "身份与权限"
description: "初始化用户、分配项目角色、管理个人 Key，并核对控制台与数据库链路。"
weight: 20
lastmod: 2026-10-29
---

用户身份、项目授权和传输加密分别配置。平台管理能力用于治理，业务数据读取仍受项目成员权限约束。

## 前置条件

准备平台管理员，以及需要授权的用户 UUID。使用独立测试项目核对权限；服务和网关的监听范围先按[部署指南]({{< relref "/docs/operations/deployment/" >}})明确。

## 1. 初始化用户与项目角色

首次启动未提供密码时，服务端生成随机管理员密码并保存为私有文件。完成首次登录和改密后，由管理员创建用户，为用户分配初始密码。

项目创建者成为 owner，再按用户 UUID 配置成员角色。项目必须保留至少一名 owner。

| 角色 | 数据能力 | 治理能力 |
|---|---|---|
| viewer | 读取共享数据与历史 | 按成员规则退出项目 |
| editor | 编辑和发布自己的工作区 | 不获得成员管理或项目审计权限 |
| owner | 读取、编辑、发布与项目审计 | 管理成员与项目生命周期 |

有效平台管理员可治理项目成员和生命周期，并查看项目元数据；该能力本身不授予要素、历史或审计读取权限。用实际成员身份分别验证允许与拒绝的操作。

## 2. 创建与轮换客户端 Key

为不同程序创建独立个人 API Key，创建时保存一次性展示的明文。Key 继承用户的项目权限，数据库保存其摘要。

轮换时先创建新 Key，在调用程序中替换并验证读取和必要写入，再撤销旧 Key。CLI 使用私有普通文件或环境变量，互斥规则见 [CLI 参考]({{< relref "/docs/reference/cli/" >}})。

用户停用、删除，或 Key 撤销与过期，会影响后续请求。权限错误时检查用户状态与成员关系，不通过共享管理员 Key 绕过授权。

## 3. 配置控制台 Session

浏览器 Cookie 中保存加密的不透明 Session ID，并使用 HttpOnly。数据库维护 Session 摘要与有效期，BFF 通过私有传输发起业务调用。

为实际访问地址配置 origin，为 Cookie 配置独立随机密钥。退出登录撤销会话；改密、管理员重置与用户状态变化的影响应纳入接入验证。具体生命周期由固定源码的身份实现定义。

## 4. 保护传输与凭据副本

服务端 HTTP 和 gRPC 支持 TLS，配置客户端 CA 后可要求 mTLS。远端 SDK 默认拒绝非回环明文；证书错误先核对 CA、主机名和有效期。

PostgreSQL 连接默认 verify-full。网关终结 TLS 时，仍需明确内部链路和可信来源。配置项见[配置参考]({{< relref "/docs/reference/configuration/" >}})。

密钥不能出现在 URL、日志、截图、静态网站产物或示例代码中。完整数据库备份也包含身份与凭据摘要，按私有恢复介质保管。

## 验证与恢复

分别验证 viewer、editor、owner 和平台管理员的允许操作与拒绝操作；撤销测试 Key 后，确认后续请求失败。检查退出后的 Session 和轮换后的应用是否符合预期。

恢复旧备份可能恢复旧凭据状态。对外重新开放前核对用户、Session 和 Key，按需要撤销或轮换；不要仅因 `/ready` 成功就开放访问。

## 实现依据

- [crates/engine/src/authentication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/authentication.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [docs/security.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/security.md)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
