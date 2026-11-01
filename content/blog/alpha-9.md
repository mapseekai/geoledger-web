---
title: "v0.3.0-alpha.9 发布：同步控制台工作区版本"
description: "修复控制台数据来源选择器在工作区保存或刷新后显示旧版本的问题。"
summary: "数据来源选择器及其列表同步显示当前工作区的草稿版本。"
weight: 5
date: 2026-11-01
tags: [Release, Console]
---

**预发布版本（Release） · 2026-11-01 · 标签 `v0.3.0-alpha.9`（提交 `7bc8b8f`）**

本版本修复 Web 控制台的数据来源选择器版本显示：工作区保存或刷新后，选择器及其列表会显示当前草稿版本。存储格式保持为 `19`，协议保持为 `geoledger/v1`。

GitHub 提供[源码预发布](https://github.com/mapseekai/geoledger/releases/tag/v0.3.0-alpha.9)，[Docker Hub](https://hub.docker.com/r/zwishing/geoledger/tags) 提供 `docker.io/zwishing/geoledger:0.3.0-alpha.9` 镜像，支持 Linux AMD64 与 ARM64。此次源码与镜像发布不包含 npm、PyPI、Go 模块标签或独立二进制包；SDK 可从[固定源码]({{< relref "/docs/reference/compatibility/" >}})构建。

[查看源码变更](https://github.com/mapseekai/geoledger/compare/v0.3.0-alpha.8...v0.3.0-alpha.9) · [控制台导览]({{< relref "/docs/guides/console/" >}})
