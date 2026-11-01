---
title: "v0.3.0-alpha.6 发布：精确页级游标与 PostGIS 表注册命名统一"
description: "统一 diff、commit、history 与 audit 的同快照页级游标终页判定，将 history 升级为页对象，并将 SDK 表接入方法统一命名为 register_table。"
summary: "统一 diff、commit、history 与 audit 的同快照页级游标终页判定，将 history 升级为页对象，并将 SDK 表接入方法统一命名为 register_table。"
weight: 20
lastmod: 2026-10-29
date: 2026-10-18
tags: [Release, API]
---

**历史版本发布（Release） · 2026-10-18 · 标签 `v0.3.0-alpha.6`**

`v0.3.0-alpha.6` 重点完善了客户端分页协议的确定性与 SDK 命名规范，并扩充了 PostGIS 生产环境的 TLS / SCRAM 安全验收门禁。

> **版本演进说明**：`alpha.6` 发布时采用的是存储格式 `16`；当前最新文档与服务已演进至 **`v0.3.0-alpha.7`（存储格式 `19`）**。升级或接入当前版本时，请以 **[版本与兼容性]({{< relref "/docs/reference/compatibility/" >}})** 为准。

## 1. 同快照页级游标：告别“靠返回条数猜测终页”

在早期版本中，客户端遍历分页时往往需要根据“本页返回条数是否小于 `limit`”来判断是否还有下一页，当总条数恰好是 `limit` 的整数倍时不得不额外发起一次空页请求。

自 `v0.3.0-alpha.6` 起：

- **同快照仅键后续探测**：`diff`、`commit`、`history` 与 `audit` 在同一个数据库读取事务快照内探测是否存在后续键，**仅在确有后续记录时返回页级游标 `next_after`**；无论最后一页是短页还是恰好满页，终页的 `next_after` 均明确为空（`null` / `None` / `nil` / `undefined`）。
- **`history` 响应升级为页对象（Breaking）**：HTTP `history` 接口与四语言 SDK 的返回值从裸提交数组统一升级为包含 `commits` 与 `next_after`（TypeScript 为 `nextAfter`）的页对象。

## 2. PostGIS 表纳管 SDK 方法统一命名为 `register_table`

为了更准确地表达“将已有 PostGIS 业务表注册为受管数据集”的业务含义，四语言 SDK 与控制台私有动作统一调整了方法命名（Breaking）：

- **Rust / Python**：`register_table`（原 `track_table`）
- **Go**：`RegisterTable`（原 `TrackTable`）
- **TypeScript**：`registerTable`（原 `trackTable`）

底层 HTTP / gRPC 协议继续复用 `create_dataset` 的 `postgis_table` 字段，无需变更 Protobuf 字段编号。

## 3. PostGIS TLS / SCRAM 门禁与单实例放行清单

- **严格的 PostgreSQL TLS 回归验证**：CI 发布门禁新增了针对强制 `hostssl` + `scram-sha-256` PostgreSQL 实例的自动化验证，全面覆盖 `sslmode=verify-full`、受信任私有 CA、错误 CA 拒绝、错误主机名拒绝以及禁止明文降级。
- **生产放行检查表**：在生产运行文档中补充了面向约 20 人团队单实例部署的上线放行检查清单（涵盖固定镜像 Digest、首次改密、冲突与幂等重放验证、异机备份恢复演练与 Prometheus 告警规则）。

## 延伸阅读

- 当前分页契约：**[分页与一致性参考]({{< relref "/docs/reference/pagination/" >}})**
- 当前 SDK 规范：**[SDK 接入与类型参考]({{< relref "/docs/reference/sdk/" >}})**
- 历史记录依据：[CHANGELOG.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/CHANGELOG.md) · [release-alpha6-validation-2026-10-18.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/release-alpha6-validation-2026-10-18.md)
