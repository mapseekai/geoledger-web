---
title: "HTTP 业务 API 参考"
linkTitle: "HTTP 业务 API"
description: "查阅 GeoLedger 公开 HTTP JSON 接口（POST /api/v1/{operation}）的完整操作目录、请求字段契约、空值语义与状态码规范。"
weight: 20
lastmod: 2026-10-29
---

除了 gRPC 与四语言 SDK 外，`geoledger-server` 还原生提供基于 JSON 的公开 **HTTP 业务 API**（默认监听在 `http://127.0.0.1:7881`）。所有业务操作统一采用 **`POST /api/v1/{operation}`** 路由，其中 `{operation}` 为 `snake_case` 操作名。

## 1. 传输协议与认证约定

- **请求头要求**：
  - `Authorization: Bearer <api-key>`：传入有效的个人 API Key（`glk_...`）。调用者身份（`subject`）完全由服务端从已验证的凭据中提取，**不允许在 JSON 请求体中伪造作者或用户身份**。
  - `Content-Type: application/json`：请求体与响应体均为 UTF-8 编码的 JSON；反序列化器启用严格校验，**拒绝未定义的未知字段**。
  - `x-request-id`（可选）：客户端或反向代理可传入自定义的请求追踪 ID（最长 128 位字母数字与 `-_.:`），未提供时服务端自动生成 UUID，并在响应头 `x-request-id` 与错误体 `request_id` 中原样返回。
- **与 gRPC 和控制台 BFF 的区别**：
  - 在公开 HTTP API 中，要素字段（`feature`）直接表示为**标准 GeoJSON 对象**（而在底层 Protobuf 线协议中，`Feature.geojson` 是字符串）。
  - 公开 HTTP JSON 中的 64 位整数（如 `revision`、`version`、属性大整数）直接以 JSON 数字传输；请使用支持 64 位整数或大数的 JSON 解析器消费，避免直接使用 JavaScript `JSON.parse` 造成超过 `2^53 - 1` 的精度丢失（注：Web 控制台内部的 `/api/session` 与 `/api/console` 属于私有 BFF 端点，请勿将其用于外部系统集成）。

## 2. 完整业务操作目录（`/api/v1/{operation}`）

以下列出公开 HTTP 业务操作的请求职责与返回结果：

| 操作名（`{operation}`） | 所属分组 | 请求体关键字段 | 响应结构与业务副作用 |
|---|---|---|---|
| `info` | 系统信息 | `{}`（空对象） | 返回服务端 `version`、`backend`、`format_version`（`19`）、`max_request_bytes`、`max_feature_bytes` 与当前用户的 `platform_admin` 标志 |
| `create_project` | 项目治理 | `name` | 创建新项目，调用者自动成为 `owner`；返回 `Project` 对象（含 `project`、`name`、`head: 0`、`role`、`state: "active"`） |
| `list_projects` | 项目治理 | `after`（可选）、`limit`（可选） | 返回当前用户可见的 `Project` 数组 |
| `get_project` | 项目治理 | `project` | 返回指定项目的元数据、当前 `head`、调用者 `role` 与 `state` |
| `rename_project` | 项目治理 | `project`、`name` | 修改项目显示名称（限 `owner` 或平台管理员），不影响项目 UUID |
| `archive_project` | 项目治理 | `project`、`archived`（布尔值） | 将项目设为只读归档（`archived: true`）或恢复为活跃状态（`archived: false`） |
| `delete_project` | 项目治理 | `project`、`confirm_name` | `confirm_name` 必须与项目名完全一致；清理数据集、工作区与版本数据，保留删除标记与不可变审计（纳管 PostGIS 原表保留） |
| `set_member` | 成员管理 | `project`、`subject`、`role` | 为指定用户 UUID（`subject`）设置 `viewer`、`editor` 或 `owner` 角色 |
| `list_members` | 成员管理 | `project`、`after`、`limit` | 返回项目的有效成员数组 `[{subject, role}]` |
| `remove_member` | 成员管理 | `project`、`subject` | 移除项目成员（或成员主动退出）；受“项目至少保留一名有效 `owner`”约束保护 |
| `create_dataset` | 数据集管理 | `project`、`name`、`geometry_type`、可选 `coordinate_dimension`、`crs`、`postgis_table` | 创建原生数据集（立即建立独立物理表与空间索引）；当提供 `postgis_table` 时，将已有 PostGIS 业务表纳管绑定为数据集 |
| `list_datasets` | 数据集管理 | `project`、`after`、`limit` | 返回项目下的数据集数组（含 `dataset`、`name`、`geometry_type`、`coordinate_dimension`、`crs`、可选 `postgis_table`） |
| `rename_dataset` | 数据集管理 | `project`、`dataset`、`name` | 修改数据集显示名称，底层物理表名与数据集 UUID 保持不变 |
| `delete_dataset` | 数据集管理 | `project`、`dataset`、`confirm_name` | `confirm_name` 必须匹配数据集名；清理该数据集的在线版本记录与自建表（若为纳管 PostGIS 表，解除绑定并保留原业务表） |
| `create_workspace` | 工作区生命周期 | `project` | 基于项目当前 `HEAD` 创建新工作区，返回 `{workspace, base_revision, version: 0, status: "open"}` |
| `list_workspaces` | 工作区生命周期 | `project`、`after`、`limit` | 返回当前用户在该项目下的工作区数组 |
| `get_workspace` | 工作区生命周期 | `project`、`workspace` | 返回工作区的 `base_revision`、当前 `version` 与 `status`（`open` / `published` / `discarded`） |
| `save` | 草稿编辑 | `project`、`workspace`、`expected_workspace_version`、`edits`、可选 `schema_edits` | 在单事务内原子保存要素增删改与字段定义意图，推进工作区 `version`，返回 `{version, changes, warnings}` |
| `discard` | 工作区生命周期 | `project`、`workspace`、`expected_workspace_version` | 丢弃开放工作区中的未发布草稿，状态变为 `"discarded"` |
| `features` | 数据与结构查询 | `project`、`dataset`、可选 `workspace` 或 `revision`、可选 `feature_id`、`bbox`、`after`、`limit` | 当指定 `feature_id` 时返回单个 GeoJSON `Feature`；否则返回 `FeatureCollection` 页对象（含 `features`、`revision`、可选 `workspace_version`、`next_after`、`crs`） |
| `schema` | 数据与结构查询 | `project`、`dataset`、可选 `workspace` 或 `revision` | 返回指定修订或工作区上下文下的字段定义 `{revision, workspace_version?, fields: [{name, type, nullable, editable}]}` |
| `workspace_summary` | 差异与冲突审阅 | `project`、`workspace` | 返回工作区变更汇总 `{version, total: {added, deleted, modified}, datasets: [...], schema_changes: [...]}` |
| `commit_summary` | 历史与审计 | `project`、`revision` | 返回指定历史修订的变更汇总 `{revision, total, datasets, schema_changes}` |
| `diff` | 差异与冲突审阅 | `project`、`workspace`、可选 `after`、`limit` | 分页返回工作区相对于 `base_revision` 的要素差异 `changes` 与字段变更 `schema_changes` |
| `conflicts` | 差异与冲突审阅 | `project`、`workspace`、可选 `after`、`limit` | 分页返回工作区相对于当前项目 `HEAD` 的三方合并冲突列表（含 `head`、`version`、`total`、`conflicts`、`next_after`） |
| `resolve` | 差异与冲突审阅 | `project`、`workspace`、`expected_workspace_version`、`expected_head`、`resolutions` | 提交冲突要素的完整最终 Feature 选择，返回 `{head, version, remaining_conflicts}` |
| `rebase` | 差异与冲突审阅 | `project`、`workspace`、`expected_workspace_version`、`expected_head`、可选 `resolutions` | 确认所有冲突已解决并将工作区 `base_revision` 更新为 `expected_head` |
| `publish` | 原子发布 | `project`、`workspace`、`expected_workspace_version`、`request_id`、`message` | 执行三方合并并在单事务内原子提交正式数据、历史、字段 DDL、回执与审计，返回 `{revision, workspace, version, status: "published", changes}` |
| `history` | 历史与审计 | `project`、可选 `after`（整数，默认 `0`）、`limit` | 按修订号升序返回提交历史页对象 `{commits: [...], next_after}` |
| `commit` | 历史与审计 | `project`、`revision`、可选 `after`、`limit` | 分页返回指定修订中发生变动的要素前后状态（`before` / `after`）与 `schema_changes` |
| `audit` | 历史与审计 | `project`、可选 `after`（整数，默认 `0`）、`limit` | 仅项目 `owner` 可读；按事件 ID 升序返回项目审计事件页对象 `{events: [...], next_after}` |
| `restore` | 历史与审计 | `project`、`revision` | 创建一个包含指定历史修订反向变更（含要素与字段）的新开放工作区，供审阅后发布 |

## 3. 核心请求字段契约与空值语义

在构造 JSON 请求体时，请重点遵循以下字段约束：

| 请求字段 | 必填 / 默认值 | 详细语义与约束 |
|---|---|---|
| `project` / `dataset` / `workspace` | 按操作必填 | 必须传入资源真实的 UUID 字符串，不能传入项目的显示名称 |
| `save.expected_workspace_version` | 必填 | 工作区当前的乐观编辑版本号（非负整数）；与服务端当前 `version` 不一致时返回 `409 Conflict` |
| `save.edits` | 默认 `[]` | 单次请求支持 `1–100` 项（若仅保存 `schema_edits` 可为空数组）。每项为 `{"dataset": "<uuid>", "feature_id": "<id>", "feature": <GeoJSON Feature 或 null>}`；`feature` 为对象时执行完整要素替换，为 `null` 时执行显式删除 |
| `save.schema_edits` | 可选 | **三态语义**：省略该字段或传 `null` 表示**保留**工作区已保存的字段意图；传空数组 `[]` 表示**撤销并清空**全部字段意图；传非空数组 `[{"dataset": "...", "add": [...], "drop": [...]}]` 表示**完整替换**字段意图 |
| `publish.request_id` | 必填 | 标识本次发布意图的 UUID。超时或断连重试时**必须原样重用同一个 `request_id`、`expected_workspace_version` 与 `message`** |
| `features.revision` 与 `workspace` | 可选且**互斥** | 两者均省略时读取项目当前 `HEAD`；传 `revision` 时读取固定历史修订快照；传 `workspace` 时读取该工作区（开放状态读取基线叠加草稿，已发布状态读取其发布修订） |
| `features.bbox` | 可选 | 长度为 4 的数值数组 `[minX, minY, maxX, maxY]`，坐标必须使用该数据集声明的原始 `crs` |
| `limit` | 默认 `100` | 分页大小，取值范围 `1–1000`（同时受单次响应编码字节预算约束） |

## 4. 请求与响应示例

### 示例 1：创建项目（`create_project`）

```sh
curl --fail-with-body http://127.0.0.1:7881/api/v1/create_project \
  -H "Authorization: Bearer $GL_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"name":"监测点演示"}'
```

响应 JSON：

```json
{
  "project": "0192d4a0-0000-7000-8000-000000000001",
  "name": "监测点演示",
  "head": 0,
  "role": "owner",
  "state": "active"
}
```

### 示例 2：原子发布工作区（`publish`）

```sh
curl --fail-with-body http://127.0.0.1:7881/api/v1/publish \
  -H "Authorization: Bearer $GL_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{
    "project": "0192d4a0-0000-7000-8000-000000000001",
    "workspace": "0192d4a0-0000-7000-8000-000000000002",
    "expected_workspace_version": 1,
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "新增示例监测点"
  }'
```

## 5. HTTP 状态码与错误处理规范

当请求失败时，服务端返回对应的 HTTP 状态码，并在 JSON 响应体的 `error` 对象中提供 `code`、`message`、`request_id`。合并冲突时，响应体顶层还包含 `conflicts` 等冲突摘要字段：

| HTTP 状态码 | 对应业务错误码（`code`） | 典型触发原因 | 客户端处理建议 |
|---|---|---|---|
| `400` / `422` | `invalid_argument` | 未知 JSON 字段、几何类型/维度不匹配、坐标非有限数、属性包含 `U+0000` 或保留键 | 修正请求参数或 GeoJSON 数据后重新提交 |
| `401` | `unauthenticated` | 缺少 Bearer Token、API Key 已撤销/过期，或所属用户已被停用 | 检查并更新有效 API Key |
| `403` | `permission_denied` | 普通用户在 `GL_PROJECT_CREATION=admins` 下创建项目、超出项目配额，或角色权限不足 | 核对项目 RBAC 角色与平台创建策略 |
| `404` | `not_found` | 目标项目/数据集/工作区不存在，或调用者无权访问该资源（非项目成员或非工作区所有者） | 核对资源 UUID、项目成员关系与工作区归属 |
| `409` | `conflict` | 工作区版本不匹配、存在未解决的三方合并冲突、`stale_resolution`、`request_id payload mismatch`、向已归档项目写入、或移除最后一名 `owner` | 根据具体消息刷新工作区、分页处理冲突，或使用原始负载重试发布 |
| `413` | `resource_exhausted` | 单次请求体或单页编码响应超出 `64 MiB` 字节预算 | 减小保存批次或调小分页 `limit` |
| `429` | `busy` | 并发执行槽/内存池耗尽、数据库锁不可用，或触发 IP / Subject 速率限制（响应附带 `Retry-After: 1`） | 降低客户端并发度，按退避策略重试（发布重试需保留原 `request_id`） |
| `503` | `unavailable` | 服务或底层数据库暂时不可用 | 检查 `/ready` 状态与数据库健康度；若为 `publish` 调用需按结果未知处理 |
| `504` / `408` | `deadline_exceeded` | 请求期限耗尽 | 缩小查询范围；**若为 `publish` 调用，请使用原 `request_id` 重放确认结果** |

## 6. 服务发现、健康检查与监控端点

除 `POST /api/v1/{operation}` 外，HTTP 监听器还提供以下 `GET` 运维端点：

- `GET /`：返回服务名称、版本号与探针路径说明。
- `GET /health`：存活检查，返回 `{"ok":true,"version":"..."}`。
- `GET /ready`：就绪检查（最多 2 秒超时），校验执行槽容量与存储后端格式，就绪时返回 `{"ok":true}`。
- `GET /metrics`：需携带 `Authorization: Bearer <api-key>`，返回 Prometheus 文本格式指标。

## 实现依据

- [crates/server/src/http.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/http.rs)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/lib.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/query.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/query.rs)
- [crates/engine/src/schema.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/schema.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [proto/geoledger/v1/geoledger.proto](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/proto/geoledger/v1/geoledger.proto)
