---
title: "编辑、审阅与发布工作区"
linkTitle: "工作区编辑与发布"
description: "在正确基线上保存完整要素，检查差异并处理并发变化。"
weight: 20
lastmod: 2026-10-29
---

使用一个工作区准备一次待发布更新。它可以包含多个数据集的草稿修改，发布后共同形成一个项目修订。

## 前置条件

准备 active 项目中的 editor 或 owner 身份，以及属于自己的开放工作区。了解[基础修订、编辑版本与 HEAD]({{< relref "/docs/start/introduction/" >}})；第一次操作请先完成[发布教程]({{< relref "/docs/start/first-publication/" >}})。

## 1. 核对读取上下文

读取工作区，记录 `base_revision`、`version` 和 `status`。确认状态为 open，数据集几何类型、维度与 CRS 与本次数据一致。

读取待修改要素的完整 Feature，再调整属性或几何。稳定字符串 ID 标识同一要素，不能用更换 ID 表达重命名。

## 2. 保存完整修改

新增或修改提交完整 Feature，删除提交显式删除操作。保存是替换式要素写入；遗漏原属性可能改变最终结果，不具有任意 JSON Patch 的保留语义。

单次要素保存支持 1-100 项修改。大文件分批保存到同一工作区，按每批成功响应更新编辑版本。字段意图与同批要素也可以原子保存，详见[字段变更指南]({{< relref "/docs/guides/schema/" >}})。

HTTP 写入携带 `expected_workspace_version`。同一批的校验、草稿、版本与审计共同提交；其中一项失败时，不能将其他项当作已经保存。

## 3. 审阅差异

先读取 summary，按数据集核对新增、修改和删除统计。再分页检查 Diff，保持同一工作区版本；有字段意图时同时审阅 `schema_changes`。

Diff 的比较基线为工作区 `base_revision`。发布后的 Diff 可从版本记录重建，表示实际合并后的发布结果，而开放草稿展示当前保存的意图。

## 4. 处理 HEAD 变化与冲突

其他工作区发布后，先查询 Conflicts，读取 Base、Current 和 Draft。对每项冲突选择完整最终 Feature，携带当前 HEAD 与编辑版本提交解决结果，再 Rebase 更新基线。

`stale_resolution` 表示旧选择不再适用于当前上下文。重新读取并审阅，不能只把预期版本改成最新值后覆盖。字段变更使用更保守的 HEAD 规则，按[字段变更指南]({{< relref "/docs/guides/schema/" >}})重新表达意图。

## 5. 发布并核对结果

填写说明，保留发布请求 ID 和原始请求，再执行 Publish。成功后记录回执中的修订，按该修订读回要素并查看提交详情。

工作区状态变为 published，后续编辑创建新工作区。响应超时或丢失时，使用[发布恢复指南]({{< relref "/docs/guides/publication-recovery/" >}})确认原意图。

## 失败处理与撤销

| 现象 | 处理 |
|---|---|
| 工作区版本不匹配 | 刷新工作区，检查其他请求结果，再决定是否重做修改 |
| 几何、属性或大小校验失败 | 修正输入；整批成功前不推进本地版本 |
| HEAD 或冲突选择失效 | 重新查询差异与冲突，审阅后解决 |
| 开放草稿不再需要 | 审阅后 Discard，清理未发布增量 |
| 已发布内容需要撤销 | 通过 Restore 创建反向工作区，见[历史指南]({{< relref "/docs/guides/history/" >}}) |

## 实现依据

- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
