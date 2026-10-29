---
title: "版本、兼容性与验证范围"
linkTitle: "版本与兼容性"
description: "区分本站源码基线、发布标签、协议版本和存储格式。"
weight: 5
lastmod: 2026-10-29
---

本站描述固定源码的行为。服务端显示的版本号相同，也可能对应不同提交；复现文档示例时，以源码提交为准。

## 适用版本

| 项目 | 固定值 | 用途 |
|---|---|---|
| 本站源码基线 | `5bf353c88cb017c8c00035fb86667dd2d7497b43` | 本站示例与实现依据 |
| 源码中的版本号 | `0.3.0-alpha.7` | 服务与 SDK 的版本标识 |
| alpha.7 发布标签 | `v0.3.0-alpha.7`，提交 `f0109c8ff424dc974421072cb2ff9b366f12c17a` | 复现该次发布的源码 |
| 存储格式 | `19` | 新库结构与已有库校验 |
| 业务协议 | gRPC `geoledger.v1`，HTTP `/api/v1` | 选择传输入口 |

源码基线包含发布标签之后的主分支修改。两者不能仅凭相同版本字符串视为相同产物。[alpha.7 发布记录]({{< relref "/blog/alpha-7/" >}})与[主分支记录]({{< relref "/blog/main-2026-10-29/" >}})分别说明其范围。

## 客户端与协议兼容性

服务端、CLI、控制台和四语言 SDK 应使用配套源码或发布产物。HTTP、gRPC 和 SDK 使用不同对象表示，尤其要核对大整数、可选字段和[分页页对象]({{< relref "/docs/reference/pagination/" >}})。

SDK 注册表分发独立于源码与镜像发布。本站采用源码安装方式；本站不据此确认某个 npm、PyPI 或其他注册表已有对应版本。

## 存储与升级边界

格式 19 需要新数据目录或新数据库，当前没有旧格式原地升级流程。不要手动改格式号、将旧数据卷挂载到新版本，或让不同版本同时使用同一数据库。

同格式恢复与可移植逻辑迁移的工具和保留范围见[备份、导出与恢复]({{< relref "/docs/operations/backup/" >}})。保留旧程序、旧库和独立备份，作为旧环境的恢复路径。

## 文档的验证范围

技术描述由固定 Git 对象中的实现与协议支持，页面末尾列出具体源码路径。产品操作流程在本次网站维护中仅按源码核对，尚未连接业务实例重跑，因此标为待环境验证的操作草案。用于部署前，应在独立测试实例执行并保存结果。

站点构建、链接、内容契约与浏览器检查覆盖网站本身，不证明 GeoLedger 服务、数据库恢复或目标负载已经通过验收。示例中的坐标和要素名称用于演示。

## 截图范围

控制台截图保留原始像素，图下注明日期与可见版本。旧截图用于解释操作布局；文字以本站源码基线为准。完整来源由网站的 `data/screenshots.json` 维护。

## 实现依据

- [Cargo.toml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/Cargo.toml)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/lib.rs)
- [proto/geoledger/v1/geoledger.proto](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/proto/geoledger/v1/geoledger.proto)
- [CHANGELOG.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/CHANGELOG.md)
