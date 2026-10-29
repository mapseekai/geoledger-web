---
title: "教程：完成第一次发布"
linkTitle: "第一次发布"
description: "用合成监测点观察草稿、发布回执、固定修订读取与撤销。"
weight: 30
lastmod: 2026-10-29
---

本教程创建一个点要素，发布两次属性变化，再生成一次反向工作区。完成后，你可以区分未发布草稿、共享修订与撤销提交。

## 前置条件

完成[快速开始]({{< relref "/docs/start/quickstart/" >}})，以可创建项目的用户登录独立测试控制台。所有名称与坐标均为合成示例。

## 1. 创建项目和数据集

创建项目“监测点演示”，再创建数据集 `stations`。几何类型选择 Point，坐标维度选择 2，CRS 选择 `EPSG:4326`。

核对数据集声明。几何类型、维度和 CRS 按数据集契约保持固定，后续编辑须遵守相同声明。

## 2. 创建工作区并保存要素

在项目中创建工作区，记录基础修订和编辑版本。在 GeoJSON 编辑入口保存以下完整 Feature：

```json
{
  "type": "Feature",
  "id": "station-001",
  "properties": {"name": "示例监测点", "status": "正常"},
  "geometry": {"type": "Point", "coordinates": [120.15, 30.27]}
}
```

保存成功后，工作区编辑版本增加，工作区读取中出现 `station-001`。此时共享修订仍保持原状态。若保存失败，先处理错误再核对版本，不能假定已保存。

## 3. 审阅差异并发布

打开工作区差异，核对该数据集的一条新增、稳定 ID、属性和几何。填写说明“新增示例监测点”，执行发布。

保存成功回执中的 `revision`，记为 R1。工作区状态变为已发布，后续编辑需要新建工作区。响应超时或断开时，使用[发布恢复流程]({{< relref "/docs/guides/publication-recovery/" >}})确认原请求。

## 4. 在新工作区修改同一要素

创建第二个工作区，读取 `station-001` 的完整 Feature，将 `status` 改为“待复核”并保存。保留原 ID、其他属性和几何。

差异应显示修改。审阅后发布，记录新的修订 R2。在正式数据中核对 `status` 为“待复核”；在 R1 下读取同一 ID 时，应得到“正常”。API 读取方式见[分页与一致性]({{< relref "/docs/reference/pagination/" >}})。

## 5. 撤销第二次提交

在历史中对 R2 执行 Restore。系统创建表达该提交反向变化的新工作区，原提交仍保留。

审阅反向差异，处理可能出现的冲突，再发布。该操作产生新的修订；随后读取 `station-001`，核对恢复后的属性。Restore 的作用范围见[历史查询与撤销]({{< relref "/docs/guides/history/" >}})。

## 完成检查

确认已发布工作区不能继续保存；R1 和 R2 可以读回不同属性；撤销通过新工作区与新修订表达。保留三次发布回执，用于核对历史与当前状态。

需要重复练习时创建另一个演示项目。误保存的开放草稿可先审阅再丢弃；已发布内容使用反向工作区处理。

## 实现依据

- [docs/console.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/console.md)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
