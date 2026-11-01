---
title: "教程：使用 Python SDK 发布并读回要素"
linkTitle: "Python SDK 教程"
description: "从源码安装官方 Python 客户端，以编程方式创建项目、保存要素草稿、原子发布并按修订号精确读取数据。"
weight: 40
lastmod: 2026-11-01
---

除了使用 Web 控制台进行交互式编辑外，你还可以通过 GeoLedger 官方提供的四语言 SDK（Rust、Go、TypeScript / Node.js、Python）将空间版本管理无缝集成到数据处理流水线或业务后端中。

本篇教程以 **Python SDK** 为例，带你编写并运行一段完整的脚本，完成项目创建、数据集声明、工作区草稿保存、差异检查、原子发布以及固定修订快照读取。

## 前置条件

1. 已完成 **[快速开始]({{< relref "/docs/start/quickstart/" >}})**，本地 gRPC 服务正监听在 `http://127.0.0.1:7882`。
2. 本机已安装 **Python 3.10 或更高版本**。
3. 在 Web 控制台（`http://localhost:3000`）左侧导航栏进入 **API Key** 页面，点击 **创建密钥**，复制生成的一次性明文密钥，并在当前终端环境中设置 `GL_API_KEY`：

```sh
export GL_API_KEY="在此替换为你在控制台创建的个人密钥"
```

> **安全提示**：API Key 明文仅在创建时展示一次。请通过环境变量或受限权限（`0600`）的私有文件加载密钥，切勿将密钥硬编码到脚本或提交至 Git 仓库。

## 步骤 1：在虚拟环境中安装 Python SDK

在 **[快速开始]({{< relref "/docs/start/quickstart/" >}})** 检出的 `geoledger` 源码仓库根目录下，创建并激活 Python 虚拟环境，直接从本地源码目录安装 `geoledger` 客户端包：

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ./sdk/python
```

## 步骤 2：编写发布与读取脚本

在当前目录新建文件 `publish_station.py`，写入以下代码：

```python
import os
from geoledger import Client

endpoint = os.environ.get("GL_ENDPOINT", "http://127.0.0.1:7882")
api_key = os.environ["GL_API_KEY"]

with Client(endpoint, api_key) as client:
    # 1. 创建项目与点要素数据集
    project = client.create_project("SDK 监测点演示")
    dataset = client.create_dataset(
        project.id,
        "stations",
        "point",
        coordinate_dimension=2,
        crs="EPSG:4326",
    )

    # 2. 创建工作区并保存一条包含 64 位大整数属性的要素
    draft = client.create_workspace(project.id)
    draft.save(
        dataset.id,
        {
            "type": "Feature",
            "id": "station-001",
            "properties": {
                "name": "示例监测点",
                "sequence": 9007199254740993,
            },
            "geometry": {
                "type": "Point",
                "coordinates": [120.15, 30.27],
            },
        },
    )

    # 3. 审阅草稿差异并原子发布
    print("草稿差异:", draft.diff())
    receipt = draft.publish("新增示例监测点")

    # 4. 使用发布回执中的修订号精确读取快照
    snapshot = client.features(
        project.id,
        dataset.id,
        revision=receipt["revision"],
    )
    print("已发布修订号:", receipt["revision"])
    print("修订快照要素:", snapshot)
```

### 代码关键点解析

- **自动维护草稿版本**：`draft` 工作区句柄在内存中自动维护乐观并发版本（`expected_workspace_version`）。每次调用 `draft.save(...)` 成功后，句柄会自动递增内部版本号。
- **精确保持 64 位整数**：请注意属性中的 `"sequence": 9007199254740993`（超过了 IEEE 754 双精度浮点数的 `2^53 - 1` 安全整数上限）。GeoLedger 在传输与存储层将 GeoJSON 作为精确文本处理，确保大整数在保存、合并和读取后分毫不差。
- **固定修订读取**：`client.features(..., revision=receipt["revision"])` 指定刚刚发布的修订号，后续正常发布不会改变这个快照。数据集或项目被删除时，相关历史可能被清理；版本历史不能替代独立备份。

## 步骤 3：运行脚本并验证结果

在激活了虚拟环境的终端中执行脚本：

```sh
python publish_station.py
```

运行成功后，终端会依次输出：
1. **草稿差异（`diff`）**：包含 `stations` 数据集中 `station-001` 的新增记录及 `base` / `draft` 对比。
2. **已发布修订号**：`1`。
3. **修订快照要素**：响应的 `features` 列表包含 `station-001`，其 `sequence` 属性完整保留为整数 `9007199254740993`。

此时你也可以打开 Web 控制台，在项目列表中找到 `SDK 监测点演示`，在地图上查看刚刚由 Python 脚本发布的监测点及其版本历史。

## 生产环境集成建议

将 SDK 接入正式业务系统时，建议进一步关注以下三个方面：

1. **异常处理与发布恢复**：SDK 抛出的 `GeoLedgerError` 包含业务错误码 `code`、`request_id` 以及布尔标志 `uncertain`。当 `publish` 因网络超时返回 `uncertain=True` 时，请勿直接重跑整个脚本创建新工作区，而应在原 `draft` 句柄上再次调用 `draft.publish("新增示例监测点")` 或使用持久化的 `pending_publication` 意图恢复结果。详见 **[确认与恢复发布]({{< relref "/docs/guides/publication-recovery/" >}})**。
2. **游标分页遍历**：当数据集要素或历史记录较多时，使用服务端返回的 `next_after` 游标并在后续请求中固定首屏 `revision`。详见 **[分页与一致性参考]({{< relref "/docs/reference/pagination/" >}})**。
3. **多语言客户端支持**：如果你使用 Rust、Go 或 TypeScript / Node.js，请查阅 **[SDK 接入与类型参考]({{< relref "/docs/reference/sdk/" >}})**。

## 附：四语言 SDK 核心操作对照速查

下表中的 `p_id` 和 `d_id` 是项目、数据集 UUID 字符串，`feature` 是带字符串 `id` 的 GeoJSON Feature，`draft` 是对应项目的工作区句柄。Go 示例将 SDK 导入为 `geoledger`，`ctx` 是 `context.Context`；TypeScript 示例从 `@geoledger/client` 导入 `Client`；Rust 示例使用 `geoledger_client` 导出的 `Client`、`Page` 和 `FeatureQuery`。表格可横向滚动。

| <span style="white-space:nowrap">业务场景</span> | Python SDK | Go SDK | TypeScript / Node.js SDK | Rust SDK |
|---|---|---|---|---|
| <strong style="white-space:nowrap">创建客户端</strong> | `Client(endpoint, api_key)` | `geoledger.Dial(endpoint, api_key)` | `new Client(endpoint, apiKey)` | `Client::connect(endpoint, api_key).await?` |
| <strong style="white-space:nowrap">创建工作区</strong> | `client.create_workspace(p_id)` | `client.CreateWorkspace(ctx, p_id)` | `await client.createWorkspace(p_id)` | `client.create_workspace(p_id).await?` |
| <strong style="white-space:nowrap">保存要素</strong> | `draft.save(d_id, feature)` | `draft.Save(ctx, d_id, feature)` | `await draft.save(d_id, feature)` | `draft.save(d_id, feature).await?` |
| <strong style="white-space:nowrap">差异审阅</strong> | `draft.diff()` | `draft.Diff(ctx, geoledger.Page{})` | `await draft.diff()` | `draft.diff(Page::default()).await?` |
| <strong style="white-space:nowrap">原子发布</strong> | `draft.publish(message)` | `draft.Publish(ctx, message)` | `await draft.publish(message)` | `draft.publish(message).await?` |
| <strong style="white-space:nowrap">固定快照读取</strong> | `client.features(p_id, d_id, revision=rev)` | `client.Features(ctx, p_id, d_id, geoledger.FeatureQuery{Revision: &rev})` | `await client.features(p_id, d_id, { revision: rev })` | `client.features(p_id, d_id, FeatureQuery { revision: Some(rev), ..Default::default() }).await?` |

固定快照中的 `rev` 在 Go 和 Rust 中是 `int64` / `i64`，在 TypeScript 中是 `bigint`。Go 方法返回值和 `error`，实际代码需要检查错误并在用完后关闭客户端；Rust 的保存与发布需要可变的 `draft`，且 `save` 接收 `serde_json::Value`。查询和差异都是分页结果，完整示例与续页方式见 **[SDK 接入与类型参考]({{< relref "/docs/reference/sdk/" >}})**。

## 实现依据

- [sdk/python/pyproject.toml](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/python/pyproject.toml)
- [sdk/python/geoledger/__init__.py](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/python/geoledger/__init__.py)
- [sdk/python/tests/smoke.py](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/python/tests/smoke.py)
- Go：[client.go](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/go/client.go) · [workspace.go](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/go/workspace.go) · [models.go](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/go/models.go)
- TypeScript：[index.ts](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/ts/src/index.ts) · [models.ts](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/ts/src/models.ts)
- Rust：[lib.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/rust/src/lib.rs) · [models.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/rust/src/models.rs)
