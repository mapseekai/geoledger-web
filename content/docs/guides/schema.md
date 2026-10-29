---
title: "新增与删除版本化字段"
linkTitle: "字段增删"
description: "在工作区保存完整字段意图，并与要素修改一起审阅和发布。"
weight: 40
lastmod: 2026-10-29
---

字段变更通过工作区表达。新增、删除字段与相关要素在同一次发布事务中提交，历史读取可使用对应修订的字段定义。

## 前置条件与支持范围

准备自己的开放工作区与 editor 或 owner 权限。先读取当前 Schema，记录工作区基础修订和版本。

| 操作 | 支持范围 | 限制 |
|---|---|---|
| 新增字段 | string、number、integer、boolean、json | 新字段可空，没有 SQL 默认表达式 |
| 删除字段 | 可恢复的普通可空属性字段 | PostGIS 列的默认值、索引、约束和依赖会限制删除 |
| 重命名或变更类型 | 不支持 | 使用明确的数据迁移方案 |
| 修改主键、几何、CRS、维度 | 不属于字段意图 | 遵守数据集固定契约 |

字段删除不使用 CASCADE 隐式移除依赖。字段发布可能触及整张数据集，应在测试副本上评估实际成本。

## 1. 保存完整字段意图

字段意图相对工作区基础修订表达完整目标，不是逐条 DDL 命令。HTTP 在 `save` 请求中提供 `schema_edits`，SDK 使用 `save_changes` / `saveChanges` / `SaveChanges`。

以下是字段意图数组示意，为测试数据集增加 note 字段，删除 gone 字段：

```json
[
  {
    "dataset": "<dataset-uuid>",
    "add": [{"name": "note", "type": "string"}],
    "drop": ["gone"]
  }
]
```

| 输入 | 结果 |
|---|---|
| 省略或 null | 保留已保存的整套字段意图 |
| 显式空数组 | 撤销全部字段意图 |
| 非空数组 | 以该数组替换完整意图 |

同一 SaveChanges 可同时带要素 edits，共用一个预期工作区版本，原子保存。纯字段修改也可以提交，不要求伪造一条要素编辑。

## 2. 读取草稿并审阅

用相同工作区读取 Schema 与要素，检查版本一致。新增字段投影为空值，被删除字段从可见属性中移除。

原始草稿仍保留隐藏值，所以撤销尚未发布的字段意图能够恢复本工作区已保存的值。审阅 Diff 和 summary 的 `schema_changes`，即使要素变化数组为空，也不能判断工作区没有修改。

## 3. 发布并核对修订

确认 HEAD 未使字段意图失效，再按[工作区发布流程]({{< relref "/docs/guides/workspaces/" >}})发布。成功后在回执修订下分别读取 Schema 与要素，并检查提交的字段变化。

发布事务共同提交必要的原表 DDL、旧正文、字段历史、要素、HEAD、回执与审计。存储中 `gl_workspace_schemas` 保存草稿意图，`gl_schema_history` 保存不可变发布定义。

## HEAD 变化与撤销

共享 HEAD 推进后，当前实现拒绝带旧字段意图的发布或 Rebase，并保留工作区。显式清空旧意图，读取当前 Schema，重新审阅并保存新的完整意图；清空前先核对需要保留的字段值。

未发布意图通过空数组撤销。已发布字段变化按[历史撤销流程]({{< relref "/docs/guides/history/" >}})审阅反向工作区，并遵守相同的列依赖约束。

## 实现依据

- [crates/engine/src/schema.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/schema.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [docs/storage.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/storage.md)
