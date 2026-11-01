---
title: "v0.3.0-alpha.4 发布：稳定用户身份、个人 API Key 与控制台会话"
description: "建立以稳定用户 UUID、Argon2id 密码哈希、个人 API Key（glk_）与数据库加密会话为核心的统一身份与访问控制体系。"
summary: "建立以稳定用户 UUID、Argon2id 密码哈希、个人 API Key（glk_）与数据库加密会话为核心的统一身份与访问控制体系。"
weight: 30
lastmod: 2026-10-29
date: 2026-10-15
tags: [Release, Security]
---

**历史版本发布（Release） · 2026-10-15 · 标签 `v0.3.0-alpha.4`**

`v0.3.0-alpha.4` 奠定了 GeoLedger 的现代身份认证与访问控制架构，并全面升级了 Web 控制台的交互体验与无障碍设计。

> **版本演进说明**：本文记录 `v0.3.0-alpha.4`（当时采用存储格式 `16`）的历史演进。当前文档对应 **`v0.3.0-alpha.7`（存储格式 `19`）**，最新安全与配置规范请参阅 **[身份与权限]({{< relref "/docs/operations/security/" >}})** 与 **[配置参数参考]({{< relref "/docs/reference/configuration/" >}})**。

## 1. 统一的用户身份与双轨凭据模型

`v0.3.0-alpha.4` 将用户身份、程序凭据与浏览器会话清晰分离：

- **稳定用户 UUID（`subject`）**：每个用户在数据库中拥有不可变的 UUID。即使后续修改登录用户名，其项目成员角色（`owner` / `editor` / `viewer`）、工作区所有权与历史审计记录也始终保持稳定关联。
- **Argon2id 密码与首次强制改密**：密码使用带随机盐的 Argon2id 哈希存储；首次启动未指定密码时自动生成私有 `initial-admin-<id>.json` 文件，首次登录及管理员重置密码后均强制要求先修改密码。
- **个人 API Key（`glk_`）与浏览器 Session 分离**：
  - **CLI 与四语言 SDK**：统一使用 `glk_` 前缀的个人 API Key（数据库仅存 SHA-256 摘要），支持独立命名、设置过期时间、多密钥并存与零停机轮换。
  - **Web 控制台**：浏览器仅持有加密的 `HttpOnly`、`SameSite=Strict` 会话 Cookie，真实会话状态与空闲/绝对过期时间由数据库集中维护，通过 Next.js BFF 私有传输调用后端引擎。

## 2. Web 控制台组件重构与沙箱化浏览器测试

- **界面与无障碍体验升级**：控制台统一采用标准组件体系，完善了键盘焦点管理、弹窗焦点恢复、未保存草稿离开提示、个人资料与 API Key 管理界面、可视化冲突解决面板以及移动端抽屉式响应式布局。
- **开启沙箱的端到端浏览器验证**：控制台 CI 的两个 Playwright 浏览器回归测试套件统一在启用 Chromium 安全沙箱的环境下执行，确保测试真实反映生产浏览器的安全约束。

## 延伸阅读

- 当前安全指南：**[配置身份、RBAC 权限与传输安全]({{< relref "/docs/operations/security/" >}})**
- 历史记录依据：[CHANGELOG.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/CHANGELOG.md)
