---
title: "查询历史快照与非破坏性撤销（Restore）"
linkTitle: "历史查询与撤销"
description: "按固定修订号重现任意历史时刻的空间要素与字段定义，或通过反向变更工作区安全撤销指定历史提交。"
weight: 50
lastmod: 2026-10-29
---

在 GeoLedger 中，每一次工作区发布都会生成一个不可变的项目级**修订号（Revision）**。你可以随时像“时间旅行”一样读取过去任意修订号下的完整数据集快照，查看单次提交的增量明细，或者在不抹去历史审计记录的前提下将某次错误提交安全回退。

> **业务撤销 vs. 灾难恢复**：本指南介绍的是日常业务层面的版本查询与提交回退（`restore` RPC）。如果是磁盘损坏、误删项目或需要从备份文件恢复整个数据库实例，请参阅运维手册中的 **[备份、导出与恢复]({{< relref "/docs/operations/backup/" >}})**。

## 前置条件

- **查询历史与固定修订读取**：需要目标项目的 `viewer`、`editor` 或 `owner` 成员权限。
- **创建并发布反向撤销工作区**：需要目标项目的 `editor` 或 `owner` 写权限。

## 步骤 1：浏览发布历史与单次提交明细

当你需要排查“某条要素是在哪次发布中被修改的”时，可以先浏览项目的提交历史列表（`history`），再查看目标修订的变更明细（`commit`）：

1. **分页查询项目历史（`history`）**：
   - 返回按修订号升序排列的 `commits` 页对象及页级游标 `next_after`。
   - 每条 `CommitInfo` 记录包含：修订号 `revision`、发布者 `subject`（用户 UUID）、发布说明 `message`、发布时间 `created_at`、来源工作区 `source_workspace` 以及发布时的基础修订 `source_base_revision`。
2. **查看提交汇总与明细（`commit_summary` 与 `commit`）**：
   - 调用 `commit_summary(project, revision)` 可快速获取该次提交在各数据集上的增删改要素计数与 `schema_changes`。
   - 调用 `commit(project, revision)` 可分页遍历该次提交中发生变化的每一条要素，对比其在发布前的状态（`before`）与发布后的状态（`after`）。

> **注意**：`commit` 接口仅返回**该次修订中发生变动的要素增量**，并非整个数据集的全量快照。若需读取该修订下的全量要素，请使用下一步的 `features` 接口。

## 步骤 2：按固定修订号读取历史快照（时间旅行查询）

要重现项目在历史修订 `R` 时的完整数据状态，只需在调用 `features` 和 `schema` 时显式传入 `revision` 参数：

```python
# 读取项目在修订号 12 时的字段定义与要素快照
schema_at_r12 = client.schema(project_id, dataset_id, revision=12)

after = ""
while True:
    page = client.features(
        project_id,
        dataset_id,
        revision=12,
        bbox=[120.10, 30.20, 120.30, 30.40],
        after=after,
        limit=100,
    )
    for feature in page["features"]:
        print(feature["id"], feature["properties"])
    if page.get("next_after") is None:
        break
    after = page["next_after"]
```

### 历史快照读取的关键规则

- **全程固定同一 `revision`**：在多页遍历或配套读取 `schema` 与 `features` 时，所有请求均传入相同的 `revision`（若首屏未传 `revision` 则默认读取当时的 `HEAD`，请从首屏响应中取出 `page["revision"]` 并在后续翻页中显式传入）。
- **使用数据集原始 CRS 的 `bbox`**：空间范围过滤参数 `bbox`（`[minX, minY, maxX, maxY]`）必须使用该数据集声明的原始坐标系（详见[分页与一致性参考]({{< relref "/docs/reference/pagination/" >}})）。
- **高效的区间组合存储**：GeoLedger 不会为每次发布复制整张数据表，而是根据 `valid_from <= revision AND (valid_to IS NULL OR revision < valid_to)` 将当前正式表中的未变动行与 `gl_history` 中的历史旧正文实时组合，既节省存储空间又保证精确的历史重现。

## 步骤 3：通过反向工作区撤销指定提交（`restore`）

如果发现历史上的某次修订（例如 `r15`）引入了错误修改，希望将其撤销，GeoLedger 提供了类似 `git revert` 的非破坏性撤销机制：

1. **调用 `restore(project, revision)`**：
   - 在控制台“版本历史”页面点击目标修订的 **撤销**，或在 SDK 中调用 `client.restore(project_id, 15)`。
   - 引擎会创建一个**新的开放工作区**，并将修订 `r15` 中所有要素变更与字段变更的**反向操作**写入该工作区草稿（例如：`r15` 新增的要素在草稿中标记为删除；`r15` 修改的要素恢复为 `r15` 之前的属性值；`r15` 删除的要素在草稿中重新恢复）。
2. **理解 `restore` 与“全库强制回滚”的区别**：
   - 假设 `r15` 修改了道路 A，随后 `r16` 修改了毫不相关的道路 B。对 `r15` 执行 `restore` **只会针对 `r15` 涉及的变更生成反向草稿**，而不会抹掉 `r16` 对道路 B 的合法更新。
3. **审阅差异、处理冲突并发布为新修订**：
   - 如果在 `r15` 之后，其他修订（如 `r16`）又继续修改了同一条道路 A，那么反向工作区在准备发布时会像普通工作区一样触发三方合并冲突提示。
   - 按 **[工作区编辑与发布]({{< relref "/docs/guides/workspaces/" >}})** 流程检查 `diff`、解决可能存在的冲突，然后填写说明（如 `"Revert r15: 恢复道路 A 原宽度"`）执行 `publish`。
   - 发布成功后会生成新的修订（如 `r17`），原修订 `r15`、`r16` 与新修订 `r17` 均完整保留在历史与审计日志中。

## 放弃撤销草稿与项目生命周期说明

- **放弃未发布的撤销**：如果你在创建反向工作区并审阅 `diff` 后决定不再执行撤销，直接对该工作区执行 **丢弃（`discard`）** 即可，不会对线上共享数据产生任何影响。
- **区分归档、丢弃与删除**：
  - `discard`（丢弃工作区）：仅清理当前未发布的个人草稿。
  - `archive_project`（归档项目）：将整个项目设为只读状态，完整保留所有数据集与历史记录。
  - `delete_dataset` / `delete_project`（删除数据集或项目）：属于不可逆的资源清理操作（会清除在线版本数据，仅保留审计记录与外部 PostGIS 原表），**切勿将删除数据集当作回退单次提交的手段**。

## 实现依据

- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [crates/engine/src/session/history.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/session/history.rs)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
