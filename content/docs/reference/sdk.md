---
title: "SDK 参考：接入方式与类型约定"
linkTitle: "SDK 接入与类型"
description: "查阅四语言客户端、源码安装入口、数值类型和工作区句柄语义。"
weight: 10
lastmod: 2026-10-29
---

四语言 SDK 通过 gRPC `geoledger.v1` 访问服务。选择与服务端配套的源码；版本对应关系见[兼容性参考]({{< relref "/docs/reference/compatibility/" >}})。首次调用的完整流程见 [Python 教程]({{< relref "/docs/start/sdk/" >}})。

## 客户端与安装入口

以下路径相对于固定提交的 GeoLedger 仓库根目录。包注册表是否已发布同版本，需要单独核实。

| 语言 | 公开入口 | 使用环境 | 源码准备 |
|---|---|---|---|
| Rust | `geoledger-client` | Tokio 异步应用 | 同工作区的 `sdk/rust` crate |
| Go | `github.com/mapseekai/geoledger/sdk/go` | Go 1.27.3+ 后端 | `sdk/go/go.mod` |
| TypeScript | `@geoledger/client` | Node.js 服务与工具 | 在 `sdk/ts` 执行 `npm ci`、`npm run build`，并由调用项目接入该本地包 |
| Python | `geoledger.Client` | Python 3.10+ | 虚拟环境中执行 `python -m pip install ./sdk/python` |

TypeScript SDK 依赖 Node.js gRPC 运行时。浏览器控制台使用 Next.js BFF 的私有 Session 传输，不直接导入 Node.js SDK。

## 连接与凭据

客户端构造时传入 endpoint 和个人 API Key。示例使用本机 `http://127.0.0.1:7882`；远端使用 HTTPS。Key 继承所属用户的项目权限。

| 客户端 | 连接入口 | 私有 CA | 显式允许非回环明文 |
|---|---|---|---|
| Rust | `Client::connect` / `connect_with` | `ConnectOptions::ca_pem` | `ConnectOptions::allow_insecure` |
| Go | `Dial` / `DialWithOptions` | 系统信任库 | `DialOptions.AllowInsecure` |
| TypeScript | `new Client(endpoint, apiKey)` | `NODE_EXTRA_CA_CERTS` 或系统信任库 | `allowInsecure` 选项 |
| Python | `Client(endpoint, api_key)` | `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH` | `allow_insecure` 参数 |

SDK 默认仅允许回环地址使用明文，默认超时为 30 秒。服务端还有独立的[资源预算与请求期限]({{< relref "/docs/reference/configuration/" >}})。

## 业务方法的职责

| 对象 | 方法族（以 Python / Rust 命名） | 结果或副作用 |
|---|---|---|
| Client | `info`、`create_project`、`project`、`projects` | 服务信息与项目管理 |
| Client | `set_member`、`members`、`remove_member`、`archive_project`、`delete_project` | 成员与生命周期 |
| Client | `create_dataset`、`register_table`、`datasets` | 自建数据集或绑定 PostGIS 原表 |
| Client | `create_workspace`、`workspace`、`workspaces` | 建立或获取工作区句柄 |
| Client | `features`、`schema`、`history`、`commit`、`audit`、`restore` | 读取版本与创建反向工作区 |
| Workspace | `save`、`save_batch`、`save_changes`、`delete` | 保存完整要素或字段意图 |
| Workspace | `features`、`schema`、`diff`、`conflicts` | 读取草稿与审阅上下文 |
| Workspace | `publish`、`resolve`、`rebase`、`discard`、`refresh` | 发布、解决冲突与维护句柄版本 |

Go 与 TypeScript 使用各语言的公开命名。完整签名由页面末尾的源码入口维护，生成的私有协议类型不作为 SDK 业务入口。

## 数值与可选字段

| 内容 | 约定 |
|---|---|
| 修订、版本与 64 位计数 | TypeScript 使用 `bigint` |
| GeoJSON 大整数 | TypeScript 使用 `parseJson` / `stringifyJson` 或直接传原始 JSON 文本 |
| Python 整数 | 保留示例中的大整数值 |
| Go 通用 JSON 解码 | 使用 `json.RawMessage` 或 `json.Decoder.UseNumber()` 保持精度 |
| `schema_edits` 缺席 / 空数组 | 分别为保留既有意图 / 清空整套意图 |
| 终页游标 | Rust / Python 为 `None`，Go 为 `nil`，TypeScript 省略 `nextAfter` |

先经过普通 `JSON.parse` 再交给 SDK，可能已经损失大整数精度。HTTP 业务接口与浏览器私有传输的整数表示也须分别处理，见 [HTTP 参考]({{< relref "/docs/reference/http/" >}})。

## 工作区句柄与错误

工作区句柄维护预期编辑版本。同一句柄的并发修改由语言机制协调：Rust 可变借用、Go 互斥锁、Python RLock、TypeScript 同句柄并发校验。多个句柄或进程仍可能遇到服务端版本冲突。

Python / TypeScript 使用 `GeoLedgerError`，Rust 使用 `Error`，Go 可用 `errors.As` 获取 `*geoledger.Error`。错误携带业务 code、message、request ID 和结果不确定性标识；完整冲突通过工作区分页查询。

`pending_publication` / `PendingPublication()` / `pendingPublication` 暴露可持久化发布意图。跨进程恢复与重试规则见[确认与恢复发布]({{< relref "/docs/guides/publication-recovery/" >}})。

## 可执行源码示例

- [Rust smoke.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/rust/examples/smoke.rs)
- [Go smoke/main.go](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/go/cmd/smoke/main.go)
- [TypeScript smoke.cjs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/ts/test/smoke.cjs)
- [Python smoke.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/tests/smoke.py)

## 实现依据

- [sdk/rust/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/rust/src/lib.rs)
- [sdk/go/client.go](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/go/client.go)
- [sdk/go/go.mod](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/go/go.mod)
- [sdk/ts/src/index.ts](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/ts/src/index.ts)
- [sdk/python/geoledger/__init__.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/geoledger/__init__.py)
- [sdk/python/pyproject.toml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/pyproject.toml)
