---
title: "确认与恢复发布"
linkTitle: "发布结果恢复"
description: "在超时、响应丢失或进程重启后，用原始发布意图确认结果。"
weight: 60
lastmod: 2026-10-29
---

发布调用超时或连接中断时，数据库可能已经提交。保留原请求 ID 与原始内容，用同一次意图确认回执，避免产生重复发布。

## 前置条件与保留内容

调用方持有原发布者身份、工作区归属，以及发布前保存的完整意图。先停止对该待确认工作区发起新的保存或新发布意图。

| 内容 | 用途 |
|---|---|
| project、workspace | 定位原始资源 |
| request_id | 标识不可变发布意图，使用原 UUID |
| expected_workspace_version | 保留原请求的编辑版本 |
| message | 保留原始说明，重试不改文案 |
| 调用身份 | 回执按 project、subject、request_id 定位 |

## 1. 区分明确拒绝与结果未知

检查业务 code、request ID 和 SDK 的 `uncertain` / `Uncertain`。明确的参数或冲突拒绝可进入修正流程；结果未知时，先确认原请求。

不要只根据网络错误、HTTP 超时或界面关闭推断数据库已回滚。发布事务的原子性和响应丢失机制见[事务解释]({{< relref "/docs/architecture/transactions/" >}})。

## 2. 在原句柄上确认

SDK 工作区句柄保留待确认请求。使用原工作区和原说明再次调用 Publish，句柄重用原始请求 ID 与内容。

HTTP 或 CLI 调用方重新提交保存的原始请求体。不要刷新后改写 expected_workspace_version，也不要生成另一个 UUID。相同 ID 搭配不同内容会得到 `request_id payload mismatch`。

## 3. 在进程重启后恢复

发布前将 SDK 暴露的 `pending_publication` / `PendingPublication()` / `pendingPublication` 意图持久化到私有存储。恢复时按对应 SDK 的类型还原，交给 `client.publish(intent)`。

Python 可用 `dataclasses.asdict`，Rust / Go 用 JSON 序列化，TypeScript 用 `stringifyJson`。TypeScript 读回时用 `parseJson`，并将 expectedWorkspaceVersion 还原为 BigInt。未保存原请求时，不能通过新建一个 ID 来证明原请求结果。

## 4. 核对回执与数据

确认响应中的修订、工作区和状态，与历史中的实际提交一致。按回执修订读回相关要素与 Schema。

对已提交意图的有效重放返回原结果，不创建第二次发布。项目归档或发布者降级为 viewer 后，已提交回执仍可重放；当前成员身份和工作区归属仍须有效。

## 身份失败与人工处理

重试遇到认证失败、权限拒绝或资源不可见时，保留未确认意图。恢复合法访问后继续确认，不能据此丢弃原请求并创建新意图。

原始意图丢失、工作区归属改变或记录无法关联时，由操作人员结合请求 ID、提交历史与审计核查。已提交内容需要撤销时，用[反向工作区]({{< relref "/docs/guides/history/" >}})生成新修订，原回执和历史继续保留。

## 实现依据

- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [sdk/python/geoledger/__init__.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/geoledger/__init__.py)
- [sdk/ts/src/index.ts](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/ts/src/index.ts)
- [docs/api.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/api.md)
