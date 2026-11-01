---
title: "工作区编辑、冲突解决与原子发布"
linkTitle: "工作区编辑与发布"
description: "全面掌握工作区草稿的分批保存、跨数据集差异审阅、三方合并冲突处理、变基（Rebase）与原子发布。"
weight: 20
lastmod: 2026-11-01
---

在 GeoLedger 中，**工作区（Workspace）** 是准备一次业务更新的隔离沙箱。你可以在同一个工作区内跨多个数据集（例如同时编辑 `roads` 道路线与 `stations` 监测点）分批保存要素修改和字段变更，经过差异审阅与冲突解决后，在单次数据库事务中将它们共同发布为一个项目级共享修订（Revision）。

## 前置条件

- 拥有目标活跃（`active`）项目的 `editor` 或 `owner` 成员角色。
- 已了解 `base_revision`（基础修订）、`version`（草稿编辑版本）与 `HEAD`（项目当前最新共享修订）的区别（参见 **[认识 GeoLedger]({{< relref "/docs/start/introduction/" >}})**）。
- 若使用 SDK 或 HTTP API，已准备好有效的个人 API Key。

## 步骤 1：创建或获取开放工作区并核对基线

每次开始一项新的编辑任务时，先创建工作区（或读取已有的开放工作区），并记录以下三个核心状态字段：

- `base_revision`：该工作区建立时所锚定的项目共享修订号。
- `version`：工作区草稿自身的乐观并发版本号（新建时为 `0`）。
- `status`：确认状态为 `"open"`（已发布 `"published"` 或已丢弃 `"discarded"` 的工作区不可继续写入）。

如果要修改已有要素，**请先在该工作区上下文下读取目标要素的完整 GeoJSON Feature**。GeoLedger 通过数据集内唯一的稳定字符串 `id` 识别要素身份——若需修改要素名称，请调整 `properties` 中的业务字段，而不要通过更换要素 `id` 来代替属性修改。

## 步骤 2：保存要素修改（全量替换与分批写入）

向工作区保存草稿时，需遵守以下写入契约：

1. **完整要素替换语义**：新增或更新要素时，必须提交包含完整 `properties` 和 `geometry` 的 GeoJSON Feature（而非局部 JSON Patch）。如果提交时省略了原有的某个属性键，该属性在合并时将被视为在草稿中被移除。
2. **显式删除操作**：删除要素时，调用 SDK 的 `delete(dataset, feature_id)`，或在批量编辑项中将 `feature` 显式设为 `null` / `None`。
3. **分批写入与乐观锁**：
   - 单次 `save` 请求支持 **1 至 100 条**要素编辑（`edits`）。导入大批量数据时，按每批不超过 100 条（控制台文件上传默认每批 20 条）依次保存到同一工作区；累计规模受存储、内存等实际条件约束。
   - 每次写入请求均携带 `expected_workspace_version`（SDK 工作区句柄会自动维护并传递该版本号）。
   - 同一批次内的所有要素校验、字段意图更新、草稿版本推进与审计记录在同一个数据库事务中执行：若其中任意一条要素几何或属性校验失败，整批写入将原子回滚，工作区 `version` 保持不变。

以下是通过 HTTP API 向工作区同时保存一条新增要素和一条删除操作的请求体示例：

```json
{
  "project": "0192d4a0-0000-7000-8000-000000000001",
  "workspace": "0192d4a0-0000-7000-8000-000000000002",
  "expected_workspace_version": 0,
  "edits": [
    {
      "dataset": "0192d4a0-0000-7000-8000-000000000003",
      "feature_id": "road-021",
      "feature": {
        "type": "Feature",
        "id": "road-021",
        "properties": {
          "name": "滨河大道北段",
          "lanes": 4,
          "width": 15
        },
        "geometry": {
          "type": "LineString",
          "coordinates": [
            [120.15, 30.27],
            [120.16, 30.28]
          ]
        }
      }
    },
    {
      "dataset": "0192d4a0-0000-7000-8000-000000000003",
      "feature_id": "road-009",
      "feature": null
    }
  ]
}
```

> **拓扑诊断警告（Warnings）**：保存请求会严格校验几何类型、坐标维度（XY/XYZ）、多边形环闭合与有限数值。对于多边形自相交等拓扑瑕疵，服务端不会篡改你的原始坐标，而是在按原样保存的同时在响应的 `warnings` 数组中返回拓扑诊断提示，并记入审计日志。

## 步骤 3：审阅差异与变更统计

在发布前，建议先全局把握变更规模，再逐页审阅明细：

1. **查看汇总统计（`workspace_summary`）**：无需传输庞大的几何坐标，即可在单次请求中获取总变更数以及按数据集分组的 `added`、`modified`、`deleted` 计数和 `schema_changes`（字段定义变更）。
2. **分页审阅要素级差异（`diff`）**：
   - `diff` 将工作区草稿（`draft`）与工作区基础修订（`base`）进行逐要素对比。
   - 遍历多页 `diff` 时，跟随服务端返回的页级游标 `next_after`，并核对每页返回的 `version` 是否保持一致（若期间工作区被再次修改，应从头重新审阅）。
   - 同时检查响应中的 `schema_changes` 数组——即使要素变更列表 `changes` 为空，只要存在字段增删意图，该工作区同样包含有效变更。

## 步骤 4：处理并发 `HEAD` 推进与三方合并冲突

在你编辑工作区期间，如果其他团队成员先行发布了新版本，项目的共享主线 `HEAD` 就会大于你工作区的 `base_revision`。此时：

- **互不重叠的修改可自动合并**：如果他人修改了其他要素，或修改了同一要素的不同顶层属性字段（例如他人将 `level` 从 `2` 改为 `3`，而你将 `width` 从 `12` 改为 `15`），发布或变基时引擎会自动执行属性级三方合并，无需人工干预。
- **冲突场景需显式裁决**：如果双方修改了同一要素的同一个属性且结果不同、双方同时修改了几何（几何作为整体空间单元比较），或一方修改而另一方删除了该要素，系统会报告合并冲突。

### 标准冲突解决流程

1. **查询冲突列表（`conflicts`）**：分页获取当前工作区相对于最新 `HEAD` 的所有冲突项。每条冲突记录均包含：
   - `fields`：发生冲突的具体字段名列表（如 `["width", "geometry"]`）。
   - `base`：共同基线版本下的要素状态。
   - `current`：当前最新共享 `HEAD` 下的要素状态。
   - `draft`：你工作区草稿中的要素状态。
   - `reason`：冲突原因说明（或 `stale_resolution` 过期标记）。
2. **提交冲突裁决（`resolve`）**：针对每条冲突要素，构造你确认的**完整最终 GeoJSON Feature**（或确认删除 `null`），并同时携带当前观察到的 `expected_head` 与 `expected_workspace_version` 提交（单批最多 100 条）：

```json
{
  "project": "0192d4a0-0000-7000-8000-000000000001",
  "workspace": "0192d4a0-0000-7000-8000-000000000002",
  "expected_workspace_version": 1,
  "expected_head": 11,
  "resolutions": [
    {
      "dataset": "0192d4a0-0000-7000-8000-000000000003",
      "feature_id": "road-021",
      "feature": {
        "type": "Feature",
        "id": "road-021",
        "properties": {
          "name": "滨河大道北段",
          "lanes": 6,
          "width": 15
        },
        "geometry": {
          "type": "LineString",
          "coordinates": [
            [120.15, 30.27],
            [120.16, 30.28]
          ]
        }
      }
    }
  ]
}
```

3. **更新工作区基准（`rebase`）**：当 `remaining_conflicts` 降为 `0` 后，调用 `rebase` 将工作区的 `base_revision` 推进到最新 `HEAD`。

> **为什么会出现 `stale_resolution`？**
> 冲突裁决依据当时的 `HEAD` 和工作区版本。如果裁决后共享 `HEAD` 推进，或工作区又成功执行 `save`，已有裁决就会标记为 `stale_resolution`（已过期）；即使变动发生在其他要素，也需要重新审阅。此时请重新读取最新的 `base` / `current` / `draft` 确认，切勿仅把版本号盲目改为最新值强行覆盖。

## 步骤 5：原子发布并验证回执

确认差异无误且无未解决冲突后，填写清晰的业务发布说明（`message`）并执行 `publish`：

1. **生成并保留 `request_id`**：每次发布请求都包含一个 UUID 格式的 `request_id`（SDK 工作区句柄会自动生成并保存该 ID）。
2. **检查发布回执（`PublishReply`）**：发布成功后，响应返回新分配的项目修订号 `revision`、工作区 ID、最终 `version`、状态 `"published"` 以及变更要素计数 `changes`。
3. **按新修订号读回验证**：使用回执中的 `revision` 调用 `features` 或 `commit` 接口，核对线上共享数据已准确更新。

## 常见异常与处理速查表

| 遇到的错误或场景 | 原因分析 | 标准处理方式 |
|---|---|---|
| `409 Conflict`（工作区版本不匹配） | 另一个客户端或并发请求已推进了该工作区的 `version` | 调用 `get_workspace` / `refresh` 刷新工作区状态，检查已有草稿差异后再决定是否继续写入 |
| `409 Conflict`（合并冲突或 `stale_resolution`） | 共享 `HEAD` 已推进且存在重叠修改，或先前的冲突裁决已过期 | 调用 `conflicts` 分页获取最新 `base` / `current` / `draft`，重新执行 `resolve` 与 `rebase` |
| `409 Conflict`（字段意图基线失效） | 工作区包含版本化字段增删意图（`schema_edits`），但期间 `HEAD` 已发生变化 | 先传空数组 `[]` 清空旧字段意图，`rebase` 到最新 `HEAD` 并读取最新 `schema` 后重新声明字段意图（详见[字段增删指南]({{< relref "/docs/guides/schema/" >}})） |
| `400` / `422`（几何或属性校验失败） | 坐标维度不符、几何类型不匹配数据集、非有限数值或属性含非法字符 | 修正输入数据后重新提交该批次（失败批次已自动回滚，无需清理残留） |
| 发布请求超时或网络断开（`uncertain`） | 客户端未收到响应，但服务端事务可能已成功提交 | **不要新建工作区重复提交**；保留原 `request_id` 与原说明重放发布请求（详见[发布结果恢复]({{< relref "/docs/guides/publication-recovery/" >}})） |
| 开放草稿不再需要 | 试验性编辑决定放弃 | 调用 `discard` 清理该工作区的未发布草稿，不影响任何已发布历史 |
| 已发布的修订发现业务错误 | 需要回退某次已生效的发布 | 调用 `restore(project, revision)` 创建反向变更工作区，审阅后发布为新修订（详见[历史查询与撤销]({{< relref "/docs/guides/history/" >}})） |

## 实现依据

- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
