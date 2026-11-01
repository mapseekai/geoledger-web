---
title: "SDK 接入与多语言类型参考"
linkTitle: "SDK 接入与类型"
description: "查阅 Rust、Go、TypeScript / Node.js 与 Python 四语言官方 SDK 的源码安装、连接认证、方法矩阵、64 位整数精度保护与错误处理规范。"
weight: 10
lastmod: 2026-11-01
---

GeoLedger 官方提供 **Rust**、**Go**、**TypeScript / Node.js** 与 **Python** 四种语言的业务 SDK。所有 SDK 均通过 gRPC（`geoledger.v1` 协议）与服务端通信，对上层暴露符合各语言习惯的业务方法与有状态工作区句柄（`Workspace`）。

如果你希望先跟随一个可运行的完整示例快速上手，请阅读 **[Python SDK 入门教程]({{< relref "/docs/start/sdk/" >}})**。

## 1. 四语言客户端与源码构建方式

以下命令与路径均相对于检出的 GeoLedger 源码仓库根目录：

| 语言 | 公开包 / 模块名 | 运行时要求 | 从源码安装或接入方式 |
|---|---|---|---|
| **Rust** | `geoledger-client` | Rust 1.88+ · Tokio 异步运行时 | 直接引用同工作区下的 `sdk/rust` crate（`cargo run -p geoledger-client ...`） |
| **Go** | `github.com/mapseekai/geoledger/sdk/go` | Go 1.27.3+ | 通过 `sdk/go/go.mod` 引入，所有网络调用均接收标准 `context.Context` |
| **TypeScript** | `@geoledger/client` | Node.js 22+（服务端 / CLI 工具） | 在 `sdk/ts` 目录执行 `npm ci && npm run build`，在 Node.js 项目中引入该本地包 |
| **Python** | `geoledger`（`geoledger.Client`） | Python 3.10+ | 在虚拟环境中执行 `python -m pip install ./sdk/python` |

> **运行环境提示**：TypeScript SDK 基于 Node.js 原生 gRPC 运行时构建（并且对超过 64 KiB 的保存请求自动启用 `SaveStream` 分块流式上传，对要素查询自动启用 `FeaturesStream` 流式下载）。浏览器前端应用请通过服务端 BFF 或 HTTP 接口接入，不要在浏览器打包器中直接导入 `@geoledger/client`。

## 2. 连接建立、TLS 与私有 CA 配置

构造客户端时需传入 gRPC 服务端地址（本地默认为 `http://127.0.0.1:7882`）与个人 API Key（`glk_...`）。

为了防止凭据在公网明文泄露，**所有 SDK 默认仅允许对本机回环地址（`127.0.0.1`、`::1`、`localhost`）使用 `http://` 明文连接**；连接远程主机时默认要求 `https://` 并校验服务端证书（默认请求超时为 30 秒）：

| 语言客户端 | 建立连接入口 | 信任私有 CA 证书的方式 | 在隔离内网显式允许非回环 `http://` |
|---|---|---|---|
| **Rust** | `Client::connect(endpoint, api_key)`<br>`Client::connect_with(endpoint, api_key, opts)` | 设置 `ConnectOptions::ca_pem` | `ConnectOptions { allow_insecure: true, ..Default::default() }` 或环境变量 `GL_ALLOW_INSECURE_TRANSPORT=true` |
| **Go** | `geoledger.Dial(endpoint, apiKey)`<br>`geoledger.DialWithOptions(endpoint, apiKey, opts)` | 操作系统信任库或 `SSL_CERT_FILE` | `DialOptions{AllowInsecure: true}` 或 `GL_ALLOW_INSECURE_TRANSPORT=true` |
| **TypeScript** | `new Client(endpoint, apiKey, timeoutMs, opts)` | 设置环境变量 `NODE_EXTRA_CA_CERTS` | `{ allowInsecure: true }` 或 `GL_ALLOW_INSECURE_TRANSPORT=true` |
| **Python** | `Client(endpoint, api_key, timeout=30.0, ...)` | 设置 `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH` | `allow_insecure=True` 或 `GL_ALLOW_INSECURE_TRANSPORT=true` |

## 3. 四语言快速接入代码对比

### Python

```python
import os
from geoledger import Client

with Client("http://127.0.0.1:7882", os.environ["GL_API_KEY"]) as client:
    project = client.create_project("城市道路网")
    dataset = client.create_dataset(project.id, "roads", "line", crs="EPSG:4326")
    draft = client.create_workspace(project.id)
    draft.save(
        dataset.id,
        {
            "type": "Feature",
            "id": "road-001",
            "properties": {"name": "滨江大道", "lanes": 4},
            "geometry": {
                "type": "LineString",
                "coordinates": [[120.15, 30.27], [120.16, 30.28]],
            },
        },
    )
    receipt = draft.publish("初始化道路要素")
```

### Rust

```rust
use geoledger_client::Client;
use serde_json::json;

let client = Client::connect(endpoint, &api_key).await?;
let project = client.create_project("城市道路网").await?;
let dataset = client.create_dataset(&project.id, "roads", "line").await?;
let mut draft = client.create_workspace(&project.id).await?;
draft.save(&dataset.id, json!({
    "type": "Feature",
    "id": "road-001",
    "properties": {"name": "滨江大道", "lanes": 4},
    "geometry": {"type": "LineString", "coordinates": [[120.15, 30.27], [120.16, 30.28]]}
})).await?;
let receipt = draft.publish("初始化道路要素").await?;
```

### Go

```go
client, err := geoledger.Dial(endpoint, apiKey)
if err != nil {
    return err
}
defer client.Close()

project, err := client.CreateProject(ctx, "城市道路网")
if err != nil {
    return err
}
dataset, err := client.CreateDataset(ctx, project.ID, "roads", "line")
if err != nil {
    return err
}
draft, err := client.CreateWorkspace(ctx, project.ID)
if err != nil {
    return err
}
_, err = draft.Save(ctx, dataset.ID, geoledger.Feature{
    Type:       "Feature",
    ID:         "road-001",
    Properties: map[string]any{"name": "滨江大道", "lanes": 4},
    Geometry:   nil,
})
if err != nil {
    return err
}
receipt, err := draft.Publish(ctx, "初始化道路要素")
```

### TypeScript / Node.js

```typescript
import { Client } from "@geoledger/client";

const client = new Client(
  process.env.GL_ENDPOINT ?? "http://127.0.0.1:7882",
  process.env.GL_API_KEY!,
);
try {
  const project = await client.createProject("城市道路网");
  const dataset = await client.createDataset(project.id, "roads", "line");
  const draft = await client.createWorkspace(project.id);
  await draft.save(dataset.id, {
    type: "Feature",
    id: "road-001",
    properties: { name: "滨江大道", exactSeq: 9007199254740993n },
    geometry: null,
  });
  const receipt = await draft.publish("初始化道路要素");
} finally {
  client.close();
}
```

## 4. 核心业务对象与方法矩阵

各语言 SDK 均围绕 `Client`（项目与全局查询）和 `Workspace`（工作区草稿句柄）两个核心对象组织方法。下表使用 Python / Rust 常见的 `snake_case` 名称概述能力；Go 与 TypeScript 的命名及参数以各语言 SDK 为准：

| 所属对象 | 方法分组 | 包含方法 | 核心职责说明 |
|---|---|---|---|
| **`Client`** | 服务与项目管理 | `info` · `create_project` · `project` · `projects` · `rename_project` · `archive_project` · `delete_project` | 查询服务版本/存储格式；创建、查询、重命名、只读归档或确认删除项目 |
| **`Client`** | 成员与权限治理 | `set_member` · `members` · `remove_member` | 按用户 `subject`（UUID）配置 `viewer` / `editor` / `owner` 角色或移除成员 |
| **`Client`** | 数据集与表纳管 | `create_dataset` · `register_table` · `datasets` · `rename_dataset` · `delete_dataset` | 创建原生数据集（指定几何类型、维度与 CRS）或纳管已有 PostGIS 业务表 |
| **`Client`** | 工作区句柄获取 | `create_workspace` · `workspace` · `workspaces` · `publish` | 创建新工作区、绑定已有工作区句柄，或重放持久化的发布意图 |
| **`Client`** | 快照、历史与撤销 | `features` · `schema` · `workspace_summary` · `commit_summary` · `history` · `commit` · `audit` · `restore` | 按修订读取要素与字段定义、查询变更统计、遍历提交与审计日志、创建反向撤销工作区 |
| **`Workspace`** | 草稿与字段保存 | `save` · `save_batch` · `save_changes` · `delete` | 单条/批量保存完整 Feature、显式删除要素，或原子保存要素与字段定义意图（`schema_edits`） |
| **`Workspace`** | 草稿读取与审阅 | `features` · `schema` · `diff` · `conflicts` | 读取叠加当前草稿后的要素与 Schema，分页审阅差异与三方合并冲突 |
| **`Workspace`** | 冲突裁决与发布 | `resolve` · `rebase` · `publish` · `discard` · `refresh` | 提交冲突解决结果、更新工作区基础修订、执行原子发布、丢弃草稿或刷新句柄版本 |

创建数据集并指定 CRS 时，Python 使用 `create_dataset(..., coordinate_dimension=2, crs="EPSG:4326")`，TypeScript 使用 `createDataset(..., 2, "EPSG:4326")`；Rust 使用 `create_dataset_with_crs`，Go 使用 `CreateDatasetWithCRS`。Rust 和 Go 也提供仅指定维度的方法。

## 5. 64 位数值精度、空值语义与并发约定

在跨语言集成时，请特别留意以下数据类型契约：

| 契约维度 | 各语言 SDK 的精确处理规则 |
|---|---|
| **修订号、版本号与 64 位计数** | 修订号和版本号在 Rust / Go 中为 `i64` / `int64`；计数类型取决于字段，例如 `Conflicts.total` 和 `PublicationResult.changes` 为 `u64` / `uint64`。Python 使用原生 `int`，TypeScript 对协议中的 64 位整数使用 `bigint` |
| **GeoJSON 属性中的 64 位大整数** | - **Python / Rust**：直接保留完整整数精度。<br>- **Go**：读取的 GeoJSON 为 `json.RawMessage`，若解码到通用 `map[string]any`，请务必使用 `json.Decoder.UseNumber()` 防止被截断为 `float64`。<br>- **TypeScript**：安全整数范围内保持 `number`，超出 `Number.MAX_SAFE_INTEGER` 的大整数自动解析为 `bigint`；请使用 SDK 导出的 `parseJson` / `stringifyJson`（或直接传原始 JSON 字符串），切勿先经过标准 `JSON.parse` 再传给 SDK |
| **字段意图 `schema_edits` 的存在性** | 调用 `save_changes` 时：传 `None`（Python/Rust）、`nil`（Go）或 `undefined`（TS）表示**保留已有字段意图**；显式传入空列表 `[]` / `Some(&[])` / 空 slice 指针表示**清空并撤销全部字段意图** |
| **分页终页游标（`next_after`）** | 当到达当前读取快照最后一页时：Python / Rust 为 `None`，Go 为 `nil`，TypeScript 中 `nextAfter` 属性省略（`undefined`） |
| **同一工作区句柄的并发安全** | 单个 `Workspace` 句柄内部维护 `expected_workspace_version` 与 `pending_publication`：Rust 通过 `&mut self` 可变借用静态保证独占，Go 使用支持 context 取消等待的锁串行化操作，Python 使用 `RLock`，TypeScript 在同句柄并发调用写操作时主动报错拦截 |
| **错误结构与幂等恢复标志** | Python / TS 抛出 `GeoLedgerError`，Rust 返回 `geoledger_client::Error`，Go 通过 `errors.As(err, &glErr)` 提取 `*geoledger.Error`。均提供 `code`、`message`、`request_id`、可选 `conflicts` 及布尔值 `uncertain`（详见[发布结果恢复]({{< relref "/docs/guides/publication-recovery/" >}})） |

## 6. 官方可执行冒烟示例（Smoke Tests）

仓库内置了覆盖四个语言的完整端到端可执行示例，可直接在源码中参考：

- **Rust**：[sdk/rust/examples/smoke.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/rust/examples/smoke.rs)
- **Go**：[sdk/go/cmd/smoke/main.go](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/go/cmd/smoke/main.go)
- **TypeScript**：[sdk/ts/test/smoke.cjs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/ts/test/smoke.cjs)
- **Python**：[sdk/python/tests/smoke.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/tests/smoke.py)

## 实现依据

- [sdk/rust/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/rust/src/lib.rs)
- [sdk/go/client.go](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/go/client.go)
- [sdk/go/go.mod](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/go/go.mod)
- [sdk/ts/src/index.ts](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/ts/src/index.ts)
- [sdk/python/geoledger/__init__.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/geoledger/__init__.py)
- [sdk/python/pyproject.toml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/pyproject.toml)
