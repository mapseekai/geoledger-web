---
title: "分页、游标与读取一致性参考"
linkTitle: "分页与一致性"
description: "查阅 GeoLedger 要素查询、差异对比、冲突列表、历史提交与审计日志的游标分页契约、快照固定规则及空间删除遮蔽语义。"
weight: 30
lastmod: 2026-11-01
---

在遍历大规模空间要素、工作区差异或版本历史时，为了避免传统 `OFFSET` 分页在大数据量下的性能衰减与并发插入漂移，GeoLedger 全面采用**基于索引键的游标分页（Keyset / Cursor Pagination）**，并结合显式的版本锚定机制保障跨页读取的一致性。

## 1. 六大分页查询契约总览

所有分页查询的 `limit` 参数默认值均为 **`100`**，允许范围为 **`1–1000`**（同时受单次响应编码字节预算 `GL_MAX_RESPONSE_BYTES` 约束）：

| 查询操作 | 响应集合字段 | 游标（`after` / `next_after`）类型与含义 | 跨页读取的一致性要求 |
|---|---|---|---|
| **`features`** | `features` 数组（HTTP 返回 `FeatureCollection`，SDK 返回页对象） | 字符串游标（最后一条要素的 `feature_id`） | **已发布数据**：首屏获取 `revision` 后，后续每页必须显式传回同一 `revision`。<br>**开放工作区**：每页核对返回的 `workspace_version` 未发生改变 |
| **`diff`** | `changes` + `schema_changes` | 复合字符串游标（`dataset/feature_id`） | 保持同一 `workspace`，且核对每页返回的 `version`（草稿编辑版本）保持一致 |
| **`conflicts`** | `conflicts`（附带 `head`、`version`、`total`） | 复合字符串游标（`dataset/feature_id`） | 保持同一 `workspace`，且核对每页返回的 `head` 与 `version` 未变 |
| **`commit`** | `changes` + `schema_changes` | 复合字符串游标（`dataset/feature_id`） | 始终传入同一个目标历史 `revision` |
| **`history`** | `commits` | 64 位整数游标（最后一条记录的 `revision`，按 `revision > after` 升序） | 每次请求在独立快照中读取；可通过保存最后观察到的 `revision` 轮询增量提交 |
| **`audit`** | `events` | 64 位整数游标（最后一条记录的 `id`，按 `id > after` 升序） | 仅项目 `owner` 可读；每次请求在独立快照中读取，可保存最后 `id` 轮询新事件 |

> **特殊说明**：
> 1. 当 `features` 传入 `feature_id` 时，HTTP 返回带查询元数据的单个 GeoJSON `Feature`；再次保存前需按 [HTTP 业务 API]({{< relref "/docs/reference/http/" >}}) 提取 Feature 字段。gRPC、`gl call` 与四语言 SDK 返回包含该要素的 `features` 数组的页对象。
> 2. HTTP 的 `list_projects`、`list_datasets`、`list_members` 与 `list_workspaces` 返回资源数组；gRPC 和 `gl call` 分别用 `projects`、`datasets`、`members`、`workspaces` 字段包装。SDK 便捷方法返回各语言的资源列表。

## 2. 精确的终页判定信号（`next_after`）

GeoLedger 的存储层（包括 `diff`、`commit`、`history`、`audit` 与 `features`）会在**同一个数据库读取事务快照内**使用轻量级仅键探测（Key-only probe）检查是否还存在后续记录：

- **请以页级 `next_after` 是否为空作为唯一的终页判断依据**，切勿根据返回数组长度是否小于 `limit` 来猜测是否还有下一页。
- 无论最后一页是空页、不足 `limit` 的短页，还是**恰好等于 `limit` 条记录的整页终页**，只要当前快照中已无后续记录，服务端都会直接返回终页信号，客户端无需再额外发起一次空页请求来确认结束。

| 客户端 / 协议环境 | 存在后续页时的表示 | 已到达终页时的表示 |
|---|---|---|
| **公开 HTTP JSON API** | `"next_after": "<cursor>"`（或整数） | `"next_after": null` |
| **Python / Rust SDK** | `next_after` 包含具体字符串或整数值 | `None` |
| **Go SDK** | `NextAfter` 为非空指针 | `nil` |
| **TypeScript SDK** | `nextAfter` 包含字符串或 `bigint` | 属性省略（`undefined`） |

## 3. 已发布快照与开放工作区的跨页一致性

### 遍历已发布共享要素（固定 `revision`）

当首屏调用 `features` 未指定 `revision` 时，服务端会自动采用当时的项目 `HEAD` 并在响应的 `revision` 字段中返回。**在进行第 2 页及后续翻页时，客户端必须显式将该 `revision` 传回**（并保持 `dataset` 与 `bbox` 不变），以确保即便在翻页期间有其他人发布了新版本，你读到的仍然是同一个历史时刻的完整无撕裂快照：

```python
revision = None
after = ""

while True:
    page = client.features(
        project.id,
        dataset.id,
        revision=revision,
        after=after,
        limit=200,
    )
    # 锁定首屏返回的修订号，供后续所有分页请求使用
    if revision is None:
        revision = page["revision"]

    for feature in page["features"]:
        process_feature(feature)

    if page.get("next_after") is None:
        break
    after = page["next_after"]
```

### 遍历开放工作区要素或差异（校验 `workspace_version`）

当指定 `workspace` 遍历未发布的开放工作区时，草稿可能会在两次分页请求之间被并发修改。因此，客户端应记录首屏响应中的 `workspace_version`（或 `diff` 中的 `version`），并在后续每一页核对该版本号是否一致；若发现版本号已递增，应丢弃已读半截数据并从头重新扫描，避免将两个不同编辑版本的草稿拼接在一起。已发布工作区的读取锚定其发布修订，但删除数据集或项目可能清理相关历史与工作区。

### 遍历历史与审计并增量轮询（`history` / `audit`）

`history` 和 `audit` 按递增整数游标分页。到达终页（`next_after is None`）仅表示“截至当前请求时刻没有更新的记录”。如果你需要持续监听项目的新发布或新审计事件，只需保存最后处理的那条记录的 `revision` 或 `id`，稍后将其作为 `after` 参数再次请求即可：

```python
after = 0
while True:
    page = client.history(project.id, after=after, limit=100)
    for commit in page["commits"]:
        print(commit["revision"], commit["message"])
        after = commit["revision"]
    if page["next_after"] is None:
        break
    after = page["next_after"]
```

## 4. OGC API Features (ISO 19168-1) 契约对照与扩展

下表借用 **OGC API Features - Part 1: Core (ISO 19168-1)** 的常见概念解释 GeoLedger 查询。GeoLedger 使用 `POST /api/v1/features` 及自己的游标和版本参数；此对照不是 OGC API Features 一致性认证。

| OGC API Features 标准概念 | GeoLedger 对应契约 | 语义说明与版本扩展 |
|---|---|---|
| **Collection (要素集合)** | 数据集（`dataset`） | 空间要素的逻辑集合，声明统一的几何类型与坐标系（CRS） |
| **Item (要素项)** | 单条要素（`Feature`） | 标准 GeoJSON 要素对象，包含不可变业务 `id`、`geometry` 与普通 `properties` |
| **FeatureCollection** | HTTP `features` 响应体 | GeoJSON 要素集容器（`type: "FeatureCollection"`），包含要素数组、修订信息和翻页游标 |
| **BBOX 空间过滤** | `bbox` 请求参数 | 仅接受数据集 CRS 中的二维范围 `[minX, minY, maxX, maxY]`；返回与范围相交的完整要素，不裁剪几何 |
| **Limit (页大小)** | `limit` 参数 | 默认 100，取值范围 1~1000 |
| **Next Link (翻页游标)** | `next_after` 字段 | 按要素键续页；固定 `revision` 或核对工作区版本才能保持跨页一致 |
| **版本化查询** | `revision` / `workspace` | 指定尚存的历史修订读取快照，或预览个人工作区草稿 |

## 5. 字段变更（`schema_changes`）与要素分页的关系

在调用 `diff`、`commit`、`workspace_summary` 或 `commit_summary` 时，请注意字段定义变更与要素分页之间的两个重要规则：

1. **不要仅凭 `changes` 数组为空判断无变更**：一次提交或工作区可能只包含新增/删除字段（纯 Schema 变更）而未修改任何要素，因此消费方必须同时检查 `changes` 与 `schema_changes`。
2. **`commit` 各页重复携带完整 `schema_changes`**：因为字段定义属于数据集级别而非单条要素级别，当分页调用固定修订的 `commit` 时，每一页（包括显式请求的空页）都会返回该修订完整的 `schema_changes` 数组。客户端在消费多页 `commit` 时，**每个修订只需处理一次 `schema_changes`**，切勿在每次要素翻页时重复应用表结构变更。

## 6. 空间范围过滤（`bbox`）与草稿删除遮蔽语义

当在开放工作区（`workspace`）上配合空间范围 `bbox`（使用数据集原始 `crs` 的 `[minX, minY, maxX, maxY]`）分页查询要素时，GeoLedger 存储引擎严格保证 **“先叠加草稿增量，再执行空间过滤（Deletion & Movement Masking）”**：

- 如果某个要素在基础修订（`base_revision`）中位于查询 `bbox` 内部，但在当前工作区草稿中被**删除**，或者其几何坐标被**修改移动到了 `bbox` 外部**，那么该要素在工作区的 `bbox` 查询结果中**绝不会露出基础修订中的旧位置**。
- 这一遮蔽语义由服务端 SQL / 空间索引查询在数据库层直接保证，客户端无需也不应依赖前端全量拉取后再做本地去重。

## 实现依据

- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/engine/src/query.rs)
- [crates/engine/src/schema.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/engine/src/schema.rs)
- [sdk/python/geoledger/__init__.py](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/sdk/python/geoledger/__init__.py)
- [sdk/ts/src/index.ts](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/sdk/ts/src/index.ts)
- [proto/geoledger/v1/geoledger.proto](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/proto/geoledger/v1/geoledger.proto)
