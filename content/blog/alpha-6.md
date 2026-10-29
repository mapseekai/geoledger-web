---
title: "alpha.6：明确分页结束与表纳管接口"
description: "页级游标统一终页语义，SDK 使用 register_table 系列方法。"
summary: "页级游标统一终页语义，SDK 使用 register_table 系列方法。"
weight: 20
lastmod: 2026-10-29
date: 2026-10-18
tags: [Release, API]
---

**Release · 2026-10-18 · v0.3.0-alpha.6**

alpha.6 主要明确客户端协议与发布验收边界：分页由服务端告知是否仍有下一页，PostGIS 表接入统一使用“注册 / 纳管”的命名。

## 分页不再依靠页长猜测

Diff、Commit、History 和 Audit 在同一读取快照中探测后续键，仅真实中间页返回页级游标。整页终页与短终页都明确结束，控制台沿用服务端判断。

History 的响应改为包含 `commits` 与 `next_after` 的页对象，四语言 SDK 同步调整。它不再是一个裸提交数组。已有调用方需要同时更新服务端、SDK 与消费逻辑。

## 表注册方法命名

Python / Rust 使用 `register_table`，Go 使用 `RegisterTable`，TypeScript 使用 `registerTable`。旧 `track_table` 系列调用需直接改名，没有保留旧别名。

底层继续沿用创建数据集与 `postgis_table` 协议。此版本发布时的存储格式仍为 16；这个历史事实不能被误用于判断当前 alpha.7 的格式要求。

## 工程验证记录

发布门禁补充 PostGIS TLS-only / SCRAM、可信 CA、错误主机名和禁止明文降级的验证，受限角色与原生恢复路径也使用证书校验连接。

源仓库中的本机测量与目标环境验收分开记录。已有测试结果不能替代任意生产环境的容量承诺。

当前接入方式见[分页与一致性]({{< relref "/docs/reference/pagination/" >}})和[API 与 SDK]({{< relref "/docs/reference/sdk/" >}})。

---

**实现依据** · 本页按 GeoLedger `0.3.0-alpha.7`、存储格式 `19` 编写，核对提交 `5bf353c`（2026-10-29）。

[CHANGELOG.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/CHANGELOG.md) · [release-alpha6-validation-2026-10-18.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/release-alpha6-validation-2026-10-18.md)
