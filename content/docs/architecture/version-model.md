---
title: "版本与可见性模型"
description: "深入解析项目 HEAD、工作区基础修订（base_revision）、草稿编辑版本（version）与历史有效期区间的读取语义。"
weight: 20
lastmod: 2026-11-01
---

任何版本控制系统都必须清晰回答两个根本问题：**“我当前的修改建立在哪个数据基线之上？”** 以及 **“当客户端发起一次查询时，究竟能看见哪些数据？”**

为了避免多人协作时草稿与线上数据相互干扰，GeoLedger 将**项目级共享修订号**（Revision）与**工作区草稿编辑版本号**（Workspace Version）设计为两套正交的版本坐标。

## 1. 核心版本对象关系

{{< version-model >}}

- **项目级共享修订（`Revision` 与 `HEAD`）**：
  修订号在整个项目（Project）范围内单调递增。一个工作区可以同时修改项目下的多个已有数据集，例如调整道路要素并新增设施要素。发布时，这些变更在同一个事务内共同生成一个新的项目级 `Revision`，并将项目的 `HEAD` 推进到该修订号。创建数据集是独立操作，不属于工作区草稿。
- **工作区双版本属性（`base_revision` 与 `version`）**：
  - `base_revision` 记录该工作区创建（或最近一次 `rebase`）时所锚定的项目共享修订号。
  - `version` 从 `0` 开始，每当向该工作区成功执行一次 `save`、`resolve`、`rebase` 或 `discard`，`version` 即递增 `1`，用于防御对同一工作区的并发覆盖写入。

## 2. 三种读取上下文的可见性规则

当调用 `features` 或 `schema` 查询数据时，GeoLedger 根据传入的选择器提供三种确定性的视图：

### 上下文 A：开放工作区读取（`workspace` 处于 `open` 状态）

开放工作区的可见状态严格定义为：

$$\text{View}(\text{Workspace}) = \text{Snapshot}(\text{base\_revision}) \oplus \Delta(\text{Workspace})$$

- **按需叠加草稿增量（Delta）**：工作区在数据库中并不会复制一份完整的数据集副本，而是仅记录被当前工作区新增、修改或标记为删除的要素增量（以及 `gl_workspace_schemas` 中的字段变更意图）。如果在后续保存中某条要素被改回了与 `base_revision` 完全相同的内容，引擎会自动移除该条冗余增量。
- **免疫他人发布的干扰**：只要你不主动执行 `rebase`，其他团队成员发布新修订推进了项目 `HEAD`，**绝不会静默改变你开放工作区的 `base_revision`**。这保证了你在编辑与审阅多页草稿期间，底层基线始终稳定可复现。
- **空间过滤下的删除与位移遮蔽**：当携带 `bbox` 查询开放工作区时，存储层先以草稿增量覆盖基础修订，再执行空间包络框过滤——已被草稿删除或已移出 `bbox` 范围的要素会准确遮蔽其在 `base_revision` 中的旧位置。

### 上下文 B：已发布工作区读取（`workspace` 处于 `published` 状态）

一旦工作区成功发布，其状态转为 `published`：

- **锚定发布修订**：通过该 `workspace` ID 查询 `features` 或 `schema` 时，服务端返回该工作区发布时生成的 `revision` 快照，包括空提交。该保证以工作区、数据集及相关历史仍然存在为前提：删除数据集或项目可能清理相关历史和工作区，详见[历史与资源生命周期]({{< relref "/docs/guides/history/" >}})。
- **草稿清理与按需重建**：发布提交后，工作区原有的临时草稿正文会被清理以释放空间；后续对该已发布工作区调用 `diff` 或 `workspace_summary` 时，系统直接从不可变的提交记录与历史表中精确重建当时的合并结果，而其 `base_revision` 仍保留原值以供追溯发布基线。

### 上下文 C：固定历史修订读取（指定 `revision` 或默认 `HEAD`）

当按共享修订号 `revision` 查询时，引擎通过**当前正式表**与**历史归档表**（`gl_history`）的半开区间组合来还原当时的完整状态。每条历史记录均带有生效区间 `[valid_from, valid_to)`，其在目标 `revision` 下可见的条件为：

```text
valid_from <= revision
AND (valid_to IS NULL OR revision < valid_to)
```

- 未被后续修订覆盖或删除的要素直接从高速正式表中读取；而在目标 `revision` 之后曾被修改或删除的要素，则从 `gl_history` 中精确提取当时有效的旧正文。
- 删除要素时，旧正文的有效区间在删除修订结束，当前表中的要素被移除，`gl_commit_changes` 记录删除前后的存在状态。`gl_history` 不需要为删除再写入一条空正文。

## 3. 稳定的资源身份与高水位修订号

- **名称与物理身份解耦**：项目 ID、数据集 ID、物理存储表名（`gl_data_<随机标识>`）以及要素 `feature_id` 均为稳定标识。重命名项目或数据集仅更新元数据表中的显示名称，绝不改变底层 UUID 或重建物理数据表。
- **高水位 `HEAD` 不复用编号**：项目的 `HEAD` 代表已分配修订号的高水位线。即使某个仅涉及单一数据集的历史修订因为后续执行了 `delete_dataset` 而被清理，项目也绝不会重新编号或复用曾经分配过的历史修订号，确保任何外部系统持有的 `(project, revision)` 引用永远不会指向错误的新数据。

## 实现依据

- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/workspace.rs)
- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/query.rs)
- [crates/engine/src/session/history.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/session/history.rs)
