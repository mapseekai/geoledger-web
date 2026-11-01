---
title: "CLI 命令行参考（gl）"
linkTitle: "CLI 接入"
description: "查阅 GeoLedger 远程命令行工具 gl 的构建方式、全局选项、凭据文件安全校验、内置子命令与通用 JSON 调用规范。"
weight: 25
lastmod: 2026-11-01
---

`gl` 是 GeoLedger 官方提供的远程命令行客户端。它底层基于 Rust SDK（`geoledger-client`）通过 gRPC 连接 `geoledger-server`，既提供了查看服务信息、项目列表、成员与历史的快捷命令，也支持通过 `gl call <operation>` 调用公开业务操作。

> **职责区分**：`gl` 是面向日常业务与自动化脚本的**远程 gRPC 客户端**；而数据库物理备份（`backup` / `restore`）与逻辑导入导出（`export` / `import` / `verify`）属于服务端本地管理命令，请通过 `geoledger-server` 执行（详见 **[备份、导出与恢复]({{< relref "/docs/operations/backup/" >}})**）。

## 1. 构建二进制与配置 API Key

### 构建 `gl`

在 GeoLedger 源码仓库根目录下运行 Cargo 构建命令：

```sh
# 开发调试构建（生成 target/debug/gl）
cargo build --locked --bins

# 生产优化构建（生成 target/release/gl；Windows 下带 .exe 后缀）
cargo build --release --locked --bins
```

如果使用 Docker Compose 统一容器，容器内已预装 `gl`，可通过 `docker compose exec geoledger gl ...` 直接调用。

### 凭据来源与严格互斥规则

为了避免不慎混用不同环境的密钥，`gl` 要求从以下两种方式中**二选一**（严格互斥）提供个人 API Key：

1. **私有凭据文件（推荐）**：通过 `--api-key-file <PATH>` 或环境变量 `GL_API_KEY_FILE` 指定一个仅包含单个 API Key 的纯文本文件（最大不超过 1,024 字节）。
   - **Unix 安全校验**：`gl` 会强制检查该文件的元数据——它必须是**普通文件（非符号链接）**，且权限必须为**仅所有者可读写（如 `0600` 或 `0400`，即 `mode & 0o077 == 0`）**。若权限过宽（如 `0644`），`gl` 将拒绝执行并提示修正权限。
2. **环境变量**：设置 `GL_API_KEY`（此时不可同时设置 `--api-key-file` 或 `GL_API_KEY_FILE`）。

如果同时提供了上述两种来源，或者两者均未提供，`gl` 会立即报错：`supply GL_API_KEY or --api-key-file exclusively`。

## 2. 全局选项与环境变量

| 命令行选项 | 对应环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `--endpoint <URL>` | `GL_ENDPOINT` | `http://127.0.0.1:7882` | 目标 `geoledger-server` 的 gRPC 监听地址 |
| `--api-key-file <PATH>` | `GL_API_KEY_FILE` | 未设置 | 私有纯文本 API Key 文件路径（与 `GL_API_KEY` 互斥） |
| *(仅环境变量)* | `GL_API_KEY` | 未设置 | 直接从环境变量读取 API Key（不提供命令行明文参数以防泄露到 `ps` 进程列表） |
| `--ca-file <PATH>` | `GL_CA_FILE` | 未设置 | 连接私有 CA 签发的 `https://` 端点时附加的 PEM 根证书文件 |
| `--allow-insecure` | `GL_ALLOW_INSECURE_TRANSPORT` | `false` | 显式允许在可信隔离内网对非回环主机使用明文 `http://` |
| `--help` / `-h` | — | — | 显示命令行帮助信息 |
| `--version` / `-V` | — | — | 显示 `gl` 客户端版本号 |

## 3. 子命令目录

| 子命令 | 参数与选项 | 等价业务操作与默认行为 |
|---|---|---|
| `gl info` | 无 | 调用 `info`，输出服务端版本、存储后端、存储格式（`19`）、请求预算与 `platform_admin` 标志 |
| `gl projects` | 无 | 调用 `list_projects`（单次请求，`limit = 100`），输出可见项目列表 |
| `gl members <PROJECT>` | `<PROJECT>`：项目 UUID | 调用 `list_members`（单次请求，`limit = 1000`），输出项目的有效成员列表 |
| `gl history <PROJECT>` | `<PROJECT>`：项目 UUID<br>`--after <REV>`：起始游标（默认 `0`） | 调用 `history`（单次请求，`limit = 100`），输出一页按修订号升序排列的提交记录与 `next_after` |
| `gl call <OPERATION>` | `<OPERATION>`：`snake_case` 操作名<br>`--file <PATH>`：JSON 输入路径（默认 `-` 表示标准输入 `stdin`） | 执行公开业务操作；输入使用普通 JSON，响应遵循 gRPC 的 JSON 表示，部分结构与 HTTP 不同 |

> **分页提示**：`projects`、`members` 与 `history` 快捷子命令仅发起单次请求，不会在终端自动循环拉取所有后续分页。当数据量超过单页上限时，请使用 `gl call` 显式传入 `after` 与 `limit` 参数（详见 **[分页与一致性参考]({{< relref "/docs/reference/pagination/" >}})**）。

例如，HTTP 的 `list_projects` 响应是项目数组，而 `gl call list_projects` 输出 `{"projects": [...]}`。指定 `feature_id` 查询时，HTTP 返回单个 Feature，`gl call features` 则将该要素放在页对象的 `features` 数组中。编写脚本时请按实际协议解析响应，参见[分页与一致性参考]({{< relref "/docs/reference/pagination/" >}})。

## 4. 常用命令示例

### 查询服务状态与项目列表

```sh
chmod 600 ./api-key
./target/debug/gl --api-key-file ./api-key info
./target/debug/gl --api-key-file ./api-key projects
```

### 使用 `gl call` 读取文件或标准输入执行业务操作

你可以将请求参数保存为 JSON 文件（如 `request.json`）：

```json
{
  "project": "0192d4a0-0000-7000-8000-000000000001",
  "limit": 100
}
```

然后通过 `--file` 传入文件，或直接通过管道（默认 `--file -`）传入标准输入：

```sh
# 方式 A：从 JSON 文件读取请求体列出数据集
./target/debug/gl --api-key-file ./api-key call list_datasets --file request.json

# 方式 B：通过管道从标准输入创建项目
printf '%s\n' '{"name":"城市管网巡检"}' \
  | ./target/debug/gl --api-key-file ./api-key call create_project
```

## 5. 标准输出、退出码与错误处理

- **成功执行（退出码 `0`）**：`gl` 将结果序列化为带缩进的格式化 JSON（Pretty-printed JSON）写入**标准输出（`stdout`）**，可直接配合 `jq` 等工具在脚本中解析。
- **执行失败（退出码 `1`）**：
  - 若为服务端返回的业务错误（`geoledger_client::Error`），`gl` 会将包含 `code`、`message`、`request_id` 与 `uncertain` 的单行 JSON 写入**标准错误（`stderr`）**。
  - 若为本地参数或文件权限错误，则向 `stderr` 输出 `gl: <错误原因>`。
- **发布超时后的安全恢复**：当通过 `gl call publish --file publish.json` 发布工作区遇到超时或网络中断时，请保留完整的 `publish.json`，使用同一身份重放。已提交且仍有读取权限时返回原回执；否则可能重新尝试发布或返回错误（详见 **[发布结果恢复]({{< relref "/docs/guides/publication-recovery/" >}})**）。

## 实现依据

- [crates/cli/src/main.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/cli/src/main.rs)
- [sdk/rust/src/lib.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/sdk/rust/src/lib.rs)
