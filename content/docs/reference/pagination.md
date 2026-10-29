---
title: "分页与一致性参考"
linkTitle: "分页与一致性"
description: "查阅各查询的游标、终页信号、修订固定与字段变更语义。"
weight: 30
lastmod: 2026-10-29
---

连续分页必须保持同一查询上下文，并使用服务端返回的页级游标。正式要素读取固定修订，开放工作区读取还需检查编辑版本。

## 分页契约

| 查询 | 页内容 | after 类型 | 连续页的约束 |
|---|---|---|---|
| Features | FeatureCollection 的 features | 要素字符串游标 | 固定首屏 revision；工作区还需核对 workspace_version |
| Diff | changes、schema_changes、version | dataset/feature_id 字符串游标 | 同一工作区且 version 未变 |
| Conflicts | conflicts、head、version、total | 字符串游标 | 保持审阅的 HEAD 和工作区版本 |
| Commit | changes、schema_changes、revision | dataset/feature_id 字符串游标 | 同一指定修订 |
| History | commits | 修订整数 | `revision > after` 升序，各请求独立读取快照 |
| Audit | events | 审计 ID 整数 | `id > after` 升序，仅项目 owner 可读 |

limit 默认 100，允许 1-1000，仍受响应编码预算约束。参数形状见 [HTTP 参考]({{< relref "/docs/reference/http/" >}})。

## 终页信号

以页级 `next_after` 为准，不根据页内数量猜测结束。空页、短终页和恰好整页终页都可返回终页信号；不用额外请求空页证明结束。

| 客户端表示 | 有后续页 | 终页 |
|---|---|---|
| 公开 HTTP JSON | next_after 含游标 | next_after 为 null |
| Python / Rust | next_after 含值 | None |
| Go | NextAfter 指向值 | nil |
| TypeScript SDK | nextAfter 含值 | 属性省略 |

单个要素查询返回 Feature，不使用集合页形状。资源列表中的项目、数据集、成员与工作区数组，不能套用 History 页对象结构。

## 正式要素与工作区读取

正式查询首屏未指定修订时使用当前 HEAD。客户端保存返回的 `revision`，后续页显式传回该值，并保持数据集、bbox 和其他筛选条件。

工作区要素使用同一工作区读取，并核对返回的 `workspace_version`。开放草稿在两页间变化时，重新开始该次扫描，避免将两个编辑版本拼成一份结果。已发布工作区固定读取自己的发布修订。

## History 遍历示例

下列 Python 片段使用已经连接的 `client` 和已有 `project`，仅展示页循环：

```python
after = 0
while True:
    page = client.history(project.id, after=after, limit=100)
    for commit in page["commits"]:
        print(commit["revision"])
    if page["next_after"] is None:
        break
    after = page["next_after"]
```

History 与 Audit 的各请求不维持冻结快照。需要后续获取新增记录时，保存最后观察到的修订或审计 ID，再显式查询；终页只描述当前请求时刻。

## 字段变化与要素分页

Diff、Commit 和 summary 含独立的 `schema_changes`。仅检查 changes 或新增、删除、修改计数，会漏掉纯字段变更。

同一固定修订的 Commit 各页重复返回完整字段变化，包括显式查询的空终页。消费方每个修订只应用一次字段元数据，不按要素页重复执行字段变化。

## 空间过滤与删除遮蔽

bbox 使用数据集原始 CRS。工作区先以草稿覆盖基础要素，再应用空间过滤；删除和移出 bbox 的要素必须遮蔽基础位置。此语义由存储读取保证，前端去重不能代替它。

## 实现依据

- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/schema.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/schema.rs)
- [sdk/python/geoledger/__init__.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/geoledger/__init__.py)
- [sdk/ts/src/index.ts](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/ts/src/index.ts)
- [proto/geoledger/v1/geoledger.proto](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/proto/geoledger/v1/geoledger.proto)
