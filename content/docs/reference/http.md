---
title: "HTTP 业务 API 参考"
linkTitle: "HTTP 业务 API"
description: "查阅公开业务操作、请求表示、空值语义与错误处理。"
weight: 20
lastmod: 2026-10-29
---

公开业务接口使用 `POST /api/v1/{operation}`，操作名为 snake_case，请求和响应为 JSON。默认本机 HTTP 地址见[配置参考]({{< relref "/docs/reference/configuration/" >}})。

## 传输约定

请求带 `Authorization: Bearer <api-key>` 和 `Content-Type: application/json`。身份来自已验证的凭据，调用方不能在 JSON 中伪造作者或 subject。请求类型拒绝未知字段。

HTTP 的 `feature` 是 GeoJSON 对象；gRPC 的 `Feature.geojson` 是编码文本。浏览器的 `/api/session` 与 `/api/console` 属于控制台 BFF 私有入口，不能替代公开业务 API。

完整 gRPC 字段定义由 [geoledger.proto](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/proto/geoledger/v1/geoledger.proto) 维护。HTTP JSON 以 Application 的请求类型和序列化实现为准，下面列出业务目录及必须区别处理的语义。

## 操作目录

表内业务路径均为 `/api/v1/` 加操作名。字段定义分别位于本页末尾链接的 `workspace.rs`、`query.rs`、`schema.rs` 和 `publication.rs`。

| 操作 | 请求职责 | 结果与副作用 |
|---|---|---|
| `info` | 空对象 | 服务版本与能力信息 |
| `create_project` | 项目名称 | 新项目，创建者成为 owner |
| `list_projects` | after、limit | 可见项目数组 |
| `get_project` | 项目 ID | 项目元数据、HEAD、角色与状态 |
| `rename_project` | 项目 ID 与名称 | 修改显示名称 |
| `archive_project` | 项目 ID 与 archived | 归档或取消归档 |
| `delete_project` | 项目 ID 与 confirm_name | 清理版本数据，保留生命周期规定的审计与标记 |
| `set_member` | 项目、用户、角色 | 设置成员角色 |
| `list_members` | 项目与分页 | 成员数组 |
| `remove_member` | 项目与用户 | 移除成员，受最后一名 owner 约束 |
| `create_dataset` | 项目与数据集声明 | 自建数据集；带 postgis_table 时绑定已有表 |
| `list_datasets` | 项目与分页 | 数据集数组 |
| `rename_dataset` | 项目、数据集与名称 | 修改显示名称 |
| `delete_dataset` | 项目、数据集与 confirm_name | 删除对应版本数据；纳管原表保留 |
| `create_workspace` | 项目 ID | 新工作区 |
| `list_workspaces` | 项目与分页 | 当前用户的工作区数组 |
| `get_workspace` | 项目与工作区 | 基础修订、编辑版本与状态 |
| `save` | 工作区版本、edits、可选 schema_edits | 原子保存草稿并推进编辑版本 |
| `discard` | 工作区与预期编辑版本 | 丢弃开放草稿 |
| `features` | 项目、数据集与查询上下文 | FeatureCollection 或单个 Feature |
| `schema` | 项目、数据集与修订或工作区 | 字段定义与读取上下文 |
| `workspace_summary` | 项目与工作区 | 要素统计与字段变化 |
| `commit_summary` | 项目与修订 | 提交统计与字段变化 |
| `diff` | 工作区与分页 | 基线与草稿差异页 |
| `conflicts` | 工作区与分页 | 当前 HEAD 下的冲突页 |
| `resolve` | 预期版本、HEAD 与完整解决结果 | 保存冲突选择 |
| `rebase` | 预期版本、HEAD 与解决结果 | 更新基础修订 |
| `publish` | 不可变请求 ID、版本与说明 | 原子发布与回执 |
| `history` | 项目、数值 after 与 limit | commits 与 next_after |
| `commit` | 项目、修订与分页 | 指定提交的 changes 与 schema_changes |
| `audit` | 项目、数值 after 与 limit | owner 可读取的 events 与 next_after |
| `restore` | 项目与指定修订 | 反向工作区，待审阅后发布 |

`register_table` 是 SDK 的便利方法，HTTP 通过 `create_dataset.postgis_table` 表达绑定。`save_changes` 是 SDK 方法，HTTP 通过 `save.schema_edits` 表达字段意图。

## 关键请求的 JSON 语义

| 请求或字段 | 必需与默认 | 约束与含义 |
|---|---|---|
| `project`、`dataset`、`workspace` | 按操作要求提供 | 使用实际资源 ID，不使用显示名称代替 |
| `save.expected_workspace_version` | 必需 | 非负工作区编辑版本，须与当前状态一致 |
| `save.edits` | 默认 `[]` | 每项含 dataset、feature_id、feature；保存完整 Feature，删除用显式 null |
| `save.schema_edits` | 可选 | 省略或 null 保留已保存的意图；`[]` 清空；非空数组替换完整意图 |
| `publish.request_id` | 必需 | UUID，同一请求 ID 必须保持原始内容 |
| `publish.expected_workspace_version` | 必需 | 发布意图记录的工作区版本 |
| `publish.message` | 必需 | 发布说明，重试时保持原文 |
| `features.revision` / `workspace` | 可选且互斥 | 都省略时读取当前 HEAD；工作区选择草稿或自己的已发布修订 |
| `features.feature_id` | 可选 | 查询单个要素，响应为 Feature |
| `features.bbox` | 可选 | `[minX,minY,maxX,maxY]`，使用数据集原始 CRS |
| 分页 `limit` | 默认 `100` | 允许 `1-1000`，仍受编码字节预算约束 |
| `schema.revision` / `workspace` | 可选且互斥 | 与配套要素查询使用相同上下文 |

HTTP 数值不要先经过会损失精度的 JavaScript Number。TypeScript SDK 用 `bigint` 保留版本与计数；浏览器私有 HTTP 将这些值编码为十进制字符串，其表示不应直接套到公开接口。

## 请求示例

下列示例会创建一个测试项目，要求私有环境中已有 `GL_API_KEY`：

```sh
curl --fail-with-body http://127.0.0.1:7881/api/v1/create_project \
  -H "Authorization: Bearer $GL_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"name":"监测点演示"}'
```

响应包含 `project`、`name`、`head`、`role` 和 `state`。不同操作可能返回对象、数组或页对象，不能统一按数组消费。

## 错误与恢复

| HTTP 状态 | 典型原因 | 调用方处理 |
|---|---|---|
| 400 / 422 | 参数或几何非法 | 修正请求 |
| 401 | 身份验证失败 | 检查 Key、用户状态与有效期 |
| 403 | 项目创建策略或配额拒绝 | 检查策略与授权 |
| 404 | 资源不存在或不可见 | 检查 ID、成员与工作区归属 |
| 409 | 版本、合并、幂等或生命周期冲突 | 按业务原因刷新与审阅 |
| 413 | 编码大小超限 | 缩小请求或页大小 |
| 429 | 执行容量或速率约束 | 控制并发，保留原写入意图 |
| 504 | 期限耗尽 | 区分明确拒绝与结果未知 |
| 503 | 存储不可用 | 诊断后端与服务状态 |

保留业务 code、message 和 request ID。发布响应丢失时沿用原始请求，处理步骤见[确认与恢复发布]({{< relref "/docs/guides/publication-recovery/" >}})。分页结束信号单独定义在[分页参考]({{< relref "/docs/reference/pagination/" >}})。

## 健康与监控入口

`GET /` 返回服务信息，`GET /health` 检查存活，`GET /ready` 检查就绪。`GET /metrics` 需要 Bearer 认证；这些入口不属于控制台 UI。

## 实现依据

- [crates/server/src/http.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/http.rs)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/lib.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/schema.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/schema.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [proto/geoledger/v1/geoledger.proto](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/proto/geoledger/v1/geoledger.proto)
