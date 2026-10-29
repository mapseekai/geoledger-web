---
title: "查询历史与撤销提交"
linkTitle: "历史查询与撤销"
description: "固定修订读取数据，并将指定提交的反向变化发布为新修订。"
weight: 50
lastmod: 2026-10-29
---

历史查询用于重现一个修订的数据，提交查询用于查看一次发布的变化。撤销通过反向工作区表达，需再次审阅与发布。

## 前置条件

准备项目读取权限和目标修订号。创建、编辑并发布反向工作区还需要写权限。数据故障恢复使用[备份流程]({{< relref "/docs/operations/backup/" >}})，本页处理业务版本操作。

## 1. 定位目标提交

在控制台历史页或 History 接口找到修订、说明、来源工作区与发布时基础修订。分页跟随页级游标，具体约束见[分页参考]({{< relref "/docs/reference/pagination/" >}})。

使用 Commit 查看这次发布的 changes 和 schema_changes。提交明细只描述变化，不能作为完整数据集快照。

## 2. 按固定修订读取

将目标修订传给 Features，并在所有后续页使用相同值。需要字段定义时，Schema 也使用同一修订；bbox 使用数据集原始 CRS。

版本存储通过当前行与历史有效期组合过去的数据，不为每次提交复制整张表。已发布工作区也固定读取自己的发布修订。

## 3. 创建反向工作区

确认要撤销的提交后，执行 `restore(project, revision)`。例如，R1 新增监测点，R2 修改另一设施；对 R1 执行 Restore 表达 R1 的反向意图，后续独立修改仍需按合并规则保留。

系统返回新的工作区。原提交继续存在；恢复某一次提交的变化，与把整个项目强制重置到过去状态的作用范围不同。

## 4. 审阅并发布

检查反向工作区的要素和字段变化。后续数据可能已变化，因此处理冲突并核对最终完整 Feature，再发布。

成功后记录新回执，核对当前状态、目标旧修订和新提交。响应未知时保留原请求，使用[发布恢复流程]({{< relref "/docs/guides/publication-recovery/" >}})。

## 放弃与生命周期操作

未发布的反向工作区可在审阅后丢弃。已发布的撤销仍是一条新提交，进一步纠正也通过新工作区处理。

项目归档保留历史并使数据只读；工作区丢弃清理未发布草稿；项目或数据集删除清理对应版本数据。执行删除前确认所需备份，不将删除用作撤销快捷方式。

## 实现依据

- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [crates/engine/src/session/history.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/session/history.rs)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
