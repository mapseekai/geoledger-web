---
title: "alpha.4：稳定用户身份与控制台会话"
description: "以用户 UUID、个人 API Key 和数据库 Session 组织访问控制。"
summary: "以用户 UUID、个人 API Key 和数据库 Session 组织访问控制。"
weight: 30
lastmod: 2026-10-29
date: 2026-10-15
tags: [Release, Security]
---

**历史版本 · 2026-10-15 · v0.3.0-alpha.4**

这一阶段将身份机制统一为稳定用户、Argon2id 密码、个人 API Key 与数据库会话。用户与成员关系使用稳定身份，客户端凭据可以独立创建、撤销和轮换。

## 浏览器与公开 SDK 各有边界

控制台通过 BFF 和私有 Session HTTP 接入，浏览器 Cookie 只保存不透明会话信息；CLI 与四语言 SDK 使用个人 API Key。业务权限由同一 Application 执行。

用户停用、密码修改与密钥撤销通过明确规则影响后续访问，历史与审计仍保留原身份引用。

## 控制台与工程检查

控制台统一组件，完善弹窗焦点恢复、未保存编辑保护、账户与冲突界面及手机布局。浏览器验证继续启用沙箱，不通过降低系统安全限制让测试通过。

此文记录历史演进。alpha.4 当时采用格式 16；当前文档对应 alpha.7 与格式 19，请以[配置参考]({{< relref "/docs/reference/configuration/" >}})和当前版本说明为准。

---

**实现依据** · 本页按 GeoLedger `0.3.0-alpha.7`、存储格式 `19` 编写，核对提交 `5bf353c`（2026-10-29）。

[CHANGELOG.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/CHANGELOG.md)
