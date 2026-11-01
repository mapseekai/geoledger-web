---
title: "三方合并与冲突处理机制"
linkTitle: "三方合并与冲突"
description: "深入解析 GeoLedger 的属性级三方合并规则、几何整体比较策略、冲突解决上下文绑定以及字段结构变更的并发控制。"
weight: 30
lastmod: 2026-11-01
---

在多人协作维护同一份空间数据集时，如果简单采用“最后写入者胜出（Last-Write-Wins）”直接用工作区草稿覆盖线上数据，就会静默冲掉其他成员刚刚发布的合法修改。

GeoLedger 在 `geoledger-core` 中实现了确定性的**三方合并**（Three-Way Merge）引擎：通过引入共同基线（`Base`），系统能够准确识别“在工作区建立之后，线上主线（`Current`）改了什么”以及“当前工作区草稿（`Draft`）改了什么”，从而安全地自动合并互不干扰的修改，并将真正的冲突交给人工审阅。

## 1. 三方合并的三个输入与属性级合并示例

当工作区准备执行 `publish` 或 `rebase`，且项目当前最新修订 `HEAD` 大于工作区的 `base_revision` 时，合并引擎会对每一条涉及变更的要素读取三个状态：

- **`Base`（共同基线）**：工作区 `base_revision` 时刻该要素的状态。
- **`Current`（当前主线）**：项目最新共享修订 `HEAD` 时刻该要素的状态。
- **`Draft`（工作区草稿）**：用户在当前工作区中提交的完整目标要素状态。

以道路数据集中的同一条要素 `road-021` 为例，假设两位编辑者几乎同时基于 `r10` 开始编辑：

| 要素字段 | `Base` (`r10`) | `Current` (他人已发布的 `r11`) | `Draft` (当前工作区草稿) | 三方合并判定结果 |
|---|---|---|---|---|
| `name` | `"滨河路"` | `"滨河路"` | `"滨河路"` | 双方均未修改，保持 `"滨河路"` |
| `level` | `2` | **`3`**（他人修改） | `2`（未修改） | **自动合并**：采用 `3`，保留他人已发布的修改 |
| `width` | `12` | `12`（未修改） | **`15`**（草稿修改） | **自动合并**：采用 `15`，合入当前草稿的修改 |
| `lanes` | `4` | **`6`**（他人修改） | **`8`**（草稿修改） | **字段冲突（Conflict）**：双方将同一属性改为了不同值，需人工裁决 |

此外，如果一方修改了要素而另一方删除了该要素（**修改-删除冲突**），或者双方在各自工作区中新增了相同 `feature_id` 但内容不同的要素（**新增-新增冲突**），系统同样会将其识别为冲突并拒绝盲目覆盖。

## 2. 为什么几何（Geometry）采用整体比较而非自动拼接顶点？

在属性字段上，GeoLedger 按顶层属性键（Key）逐个执行三方合并；但对于要素的空间几何（`geometry`），**GeoLedger 始终将其作为一个不可分割的整体单元进行比较**：

- 如果仅 `Current` 修改了几何而 `Draft` 未改几何（仅改了属性），则自动保留 `Current` 的新几何；反之若仅 `Draft` 修改了几何，则自动采用 `Draft` 的新几何。
- **一旦 `Current` 与 `Draft` 双方都对同一要素的几何做了不同的修改，系统必然触发 `geometry` 冲突**。

**设计考量**：空间几何（如折线 `LineString` 或带洞多边形 `Polygon`）不仅包含有序坐标序列与二维/三维（XY/XYZ）坐标，还承载着业务拓扑约束（如道路连通性、宗地边界闭合无重叠）。如果两个用户分别移动了同一条折线或同一个多边形的不同顶点，机械地把两人的顶点位移拼接在一起，极易产生自相交多边形或违背现实地理边界的“幽灵图形”。因此，将几何冲突整体呈现给审阅者，由审阅者明确确认最终的完整几何，是保障空间数据质量最稳妥的做法。

## 3. 冲突审阅、裁决与状态绑定循环 {#conflicts}

当存在合并冲突时，工作区遵循严谨的“查询 → 裁决 → 变基 → 发布”闭环：

{{< merge-flow >}}

### 裁决结果的上下文绑定与 `stale_resolution`

当你调用 `resolve` 提交某条冲突要素的最终状态时，请求必须同时携带：
1. `expected_head`：你审阅冲突时所依据的项目 `HEAD` 修订号。
2. `expected_workspace_version`：当前工作区的草稿版本号。

服务端在 `resolve` 时核对 `expected_head` 和 `expected_workspace_version`，并记录裁决依据的 `HEAD`。如果在你完成裁决后、正式调用 `publish` 或 `rebase` 之前：
- 其他人发布新修订，导致项目 `HEAD` 再次推进，即使该冲突要素本身没有改变；
- 或者该工作区又成功执行了 `save`，即使保存的是其他要素或字段意图；

那么此前的冲突解决记录就会被标记为 **`stale_resolution`（已过期）**，需要重新读取冲突并审阅。多次 `resolve` 可分批处理冲突；后续 `save` 会使已有裁决整体失效。

## 4. 冲突分页缓存与字段变更（Schema）的并发边界

- **高效的冲突键缓存（`gl_conflict_cache`）**：
  当一个大工作区产生数百条冲突时，为了支持翻页，GeoLedger 会在项目锁保护下按 `(project, workspace, base_revision, workspace_version, head)` 五元组生成冲突键索引与精确总数 `total`（仅缓存数据集与要素键，不冗余复制大几何正文）。只要这五个版本坐标未变，后续调用 `conflicts` 即可按复合游标定位本页冲突详情。
- **字段结构变更（`schema_edits`）不执行自动合并**：
  普通要素属性值可以按字段粒度三方合并，但新增或删除数据集字段（`schema_edits`）会影响整个数据集的表结构与历史投影。因此，当带有未发布字段意图的工作区遇到共享 `HEAD` 推进时，引擎采取保守拒绝策略（保留草稿，要求先清空旧字段意图、更新基线并核对最新 Schema 后再重新声明），避免并发 DDL 产生意外的表结构组合（操作步骤详见 **[新增与删除版本化字段]({{< relref "/docs/guides/schema/" >}})**）。

## 实现依据

- [crates/core/src/merge.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/core/src/merge.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [docs/storage.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/storage.md)
