---
title: "新增与删除版本化字段（Schema）"
linkTitle: "字段增删"
description: "在工作区中声明数据集普通属性字段的新增与删除意图，实现表结构变更与要素修改的同事务原子发布与历史回溯。"
weight: 40
lastmod: 2026-10-29
---

在空间数据演进过程中，除了要素本身的增删改外，数据集的**属性表结构**（Schema）也常常需要调整——例如为道路图层新增一个 `note`（备注）字段，并移除不再使用的 `gone` 旧字段，同时在同一批更新中为部分道路填入新的 `note` 值。

自存储格式 `19`（`v0.3.0-alpha.7`）起，GeoLedger 支持**版本化字段定义**。你可以在工作区中声明字段的新增与删除意图（`schema_edits`），与要素修改一起审阅差异、一起在单个数据库事务中原子发布，并随时按任意历史修订号查询当时的字段结构。

## 支持范围与约束边界

开始操作前，请先确认待执行的表结构变更位于受支持范围内：

| 操作类别 | 支持范围与类型映射 | 约束与边界说明 |
|---|---|---|
| **新增普通属性字段（`add`）** | 支持 5 种逻辑类型：`string`、`number`、`integer`、`boolean`、`json`（底层分别映射为 `text`、`float8`、`int8`、`bool`、`jsonb`） | 新增字段统一为**可空（`nullable = true`）**，不支持注入自定义 SQL `DEFAULT` 表达式 |
| **删除普通属性字段（`drop`）** | 支持删除普通可编辑（`editable = true`）、可空且可恢复类型的属性字段 | 若 PostGIS 纳管表的目标列上存在默认值、索引、唯一/外键/检查约束、生成列或视图依赖，系统将拒绝删除（绝不隐式执行 `DROP ... CASCADE`） |
| **字段重命名或修改类型** | 不直接作为单步 DDL 意图 | 请通过“新增目标字段 + 迁移要素属性值 + 删除旧字段”的显式工作流完成 |
| **主键、几何列、CRS 与维度** | 属于数据集核心契约（`editable = false`），不可通过 `schema_edits` 修改 | 在创建数据集时固定 |

> **性能评估建议**：发布包含字段删除或新增的工作区时，引擎需要在发布事务内归档受影响要素的旧正文（对于 PostGIS 纳管表还会同步执行原表 `ALTER TABLE`）。对于包含大量要素的数据集，建议先在测试副本上评估执行耗时。

## 步骤 1：查询当前字段定义（`schema`）

在准备字段变更前，先读取数据集在当前共享 `HEAD`（或指定工作区）下的字段定义：

- **Python**：`client.schema(project.id, dataset.id)` 或 `draft.schema(dataset.id)`
- **Rust**：`client.schema(&project.id, &dataset.id, SchemaQuery::default()).await?`
- **Go**：`client.Schema(ctx, project.ID, dataset.ID, geoledger.SchemaQuery{})`
- **TypeScript**：`await client.schema(project.id, dataset.id)`

响应包含当前生效的 `revision`、可选的 `workspace_version` 以及 `fields` 列表：

```json
{
  "revision": 3,
  "fields": [
    {
      "name": "name",
      "type": "text",
      "nullable": true,
      "editable": true
    },
    {
      "name": "gone",
      "type": "text",
      "nullable": true,
      "editable": true
    }
  ]
}
```

## 步骤 2：在工作区中保存完整字段意图（`schema_edits`）

工作区的 `schema_edits` 表达的是**相对于该工作区 `base_revision` 的完整目标状态**，而不是逐条追加的增量 DDL 命令。

你可以通过 HTTP `save` 请求的 `schema_edits` 字段，或通过四语言 SDK 的 `save_changes` / `SaveChanges` / `saveChanges` 方法，将要素修改（`edits`）与字段意图（`schema_edits`）在同一个 `expected_workspace_version` 下原子保存。如果本次只调整表结构而不修改具体要素，`edits` 传空数组 `[]` 即可。

以下是为数据集新增 `note` 字段并删除 `gone` 字段的 `schema_edits` JSON 结构示例：

```json
[
  {
    "dataset": "0192d4a0-0000-7000-8000-000000000003",
    "add": [
      {
        "name": "note",
        "type": "string"
      }
    ],
    "drop": [
      "gone"
    ]
  }
]
```

### 重点：区分“省略 / `null`”与“空数组 `[]`”

由于 `schema_edits` 代表工作区的完整字段意图，不同传参方式具有明确区分的语义：

| 传入的 `schema_edits` 值 | 对应 SDK 调用方式 | 引擎执行结果 |
|---|---|---|
| **省略字段或传 `null`** | 调用普通 `save` / `save_batch`，或在 `save_changes` 中传 `None` / `nil` / `undefined` | **保留**该工作区先前已保存的字段意图不变 |
| **显式传空数组 `[]`** | 在 `save_changes` 中传入 `[]` / `Some(&[])` / 空 slice 指针 | **撤销并清空**该工作区中所有未发布的字段意图 |
| **传入非空数组 `[...]`** | 在 `save_changes` 中传入最新数组 | **完整替换**该工作区的字段意图 |

## 步骤 3：在草稿中预览投影与审阅差异

保存字段意图后，当你在该工作区上下文下读取 `schema` 或 `features` 时，会立即看到投影效果：

- **新增字段自动补空**：读取工作区 Schema 时包含新字段 `note`；读取要素时会自动投影出新增字段（未赋值时为 `null`），你可以直接在同一次或后续保存中为要素写入 `note` 属性值。
- **被删字段隐藏但底层可恢复**：被加入 `drop` 列表的字段（如 `gone`）会从工作区可见要素属性中移除；但在工作区正式发布前，草稿底层仍保留其原始值——这意味着如果你通过传入 `schema_edits: []` 撤销了删除意图，本工作区此前保存的字段值能够无损恢复。
- **独立审阅 `schema_changes`**：调用 `diff` 或 `workspace_summary` 时，响应中的 `schema_changes` 数组会明确列出每个受影响数据集在变更前（`before`）与变更后（`after`）的完整字段列表。

## 步骤 4：原子发布与并发 `HEAD` 变更处理

确认要素差异与 `schema_changes` 均符合预期后，执行 `publish`：

- 引擎会在**同一个数据库事务**中：将受影响要素的旧正文归档至 `gl_history`，对 PostGIS 原表或自建表执行字段更新，将不可变字段快照写入 `gl_schema_history`，推进项目 `HEAD`，并记录发布回执与审计日志。
- 发布完成后，任何客户端都可以通过指定 `revision` 同时查询当时的 `schema` 与 `features`，确保历史数据与当时的表结构严格对应。

### 当共享 `HEAD` 在编辑期间推进时怎么办？

对于普通要素属性，GeoLedger 支持自动三方合并；但对于影响全表结构的 `schema_edits`，为了防止并发 DDL 产生不可预期的表结构组合，GeoLedger 采取了**保守的并发保护策略**：

如果工作区带有未发布的 `schema_edits`，且期间项目的共享 `HEAD` 已被其他工作区推进，此时直接调用 `publish` 或携带字段意图执行 `rebase` 会被明确拒绝（返回 `409 Conflict`），同时**完整保留你的工作区草稿**。请按以下步骤安全处理：

1. 调用 `save_changes` 并显式传入空数组 `schema_edits = []`，先撤销当前工作区基于旧基线的字段意图（如有需要，先记录草稿中已填写的新字段属性值）。
2. 执行 `rebase` 将工作区的 `base_revision` 更新到最新 `HEAD`。
3. 读取最新 `HEAD` 下的 `schema`，核对他人是否已经做了表结构调整，然后重新提交基于最新基线的 `schema_edits` 并发布。

### 如何撤销已发布的字段变更？

如果包含字段变更的修订已经发布，请使用 **[历史查询与撤销]({{< relref "/docs/guides/history/" >}})** 中的 `restore(project, revision)` 功能。系统会自动生成包含反向字段变更（例如重新加回被删字段并恢复受影响要素的原字段值，或移除新增字段）的新工作区，经你审阅后作为新修订发布。

## 实现依据

- [crates/engine/src/schema.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/schema.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [docs/storage.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/storage.md)
