---
title: "CLI 参考"
linkTitle: "CLI 接入"
description: "查阅 gl 的连接选项、命令、JSON 输入和退出行为。"
weight: 25
lastmod: 2026-10-29
---

`gl` 是 gRPC 远程客户端。它连接业务服务，使用用户身份执行操作；数据库备份和导入等本地管理命令属于 `geoledger-server`，见[备份指南]({{< relref "/docs/operations/backup/" >}})。

## 构建与身份

在文档对应的源码根目录执行 `cargo build --locked --bins`，生成 `target/debug/gl`。发布构建使用 `cargo build --release --locked --bins`；Windows 程序带 `.exe` 后缀。

API Key 从 `GL_API_KEY` 或私有纯文本文件中选择一种来源。两者同时设置或都未提供时，CLI 拒绝执行。Unix 文件要求为私有普通文件，不能是符号链接。

## 全局选项

| 选项 | 环境变量 | 默认值 | 用途 |
|---|---|---|---|
| `--endpoint` | `GL_ENDPOINT` | `http://127.0.0.1:7882` | gRPC 服务地址 |
| `--api-key-file` | `GL_API_KEY_FILE` | 未设置 | 私有 API Key 文件 |
| 无命令行 Key 参数 | `GL_API_KEY` | 未设置 | 与凭据文件互斥的 Key 来源 |
| `--ca-file` | `GL_CA_FILE` | 未设置 | 私有 CA PEM 文件 |
| `--allow-insecure` | `GL_ALLOW_INSECURE_TRANSPORT` | `false` | 显式允许非回环 HTTP |
| `--help` | 无 | 无 | 输出命令帮助 |
| `--version` | 无 | 无 | 输出客户端版本 |

## 命令目录

| 命令 | 参数 | 输出与范围 |
|---|---|---|
| `info` | 无 | 版本、后端和请求规格 |
| `projects` | 无 | 一次请求的可见项目列表，limit 为 100 |
| `members <project>` | 项目 UUID | 一次请求的成员列表，limit 为 1000 |
| `history <project>` | `--after`，默认 `0` | 一页提交记录，limit 为 100 |
| `call <operation>` | `--file`，默认 `-` | 执行指定业务操作，JSON 形状见 HTTP 业务参考 |

快捷列表命令不自动遍历所有页。需要完整扫描时，通过 `call` 显式传入分页参数，并遵守[游标契约]({{< relref "/docs/reference/pagination/" >}})。

## 文件与标准输入

以下示例使用已经保存的测试 Key 文件，不包含密钥明文：

```sh
chmod 600 ./api-key
./target/debug/gl --api-key-file ./api-key info
./target/debug/gl --api-key-file ./api-key projects
./target/debug/gl --api-key-file ./api-key call list_datasets --file request.json
```

`request.json` 的示意内容如下，先将占位值替换为真实测试项目 UUID：

```json
{"project": "<project-uuid>", "limit": 100}
```

`--file -` 从标准输入读取 JSON。凭据不得放在 URL 查询参数中。

## 输出与失败

成功结果以格式化 JSON 写入标准输出。失败写入标准错误并以状态码 `1` 退出；业务错误保留 SDK 错误内容。

`call publish` 的结果未知时，保留输入文件、原请求 ID 与原始内容，按[发布恢复指南]({{< relref "/docs/guides/publication-recovery/" >}})确认结果。更换 UUID 会产生新的发布意图。

## 实现依据

- [crates/cli/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/cli/src/main.rs)
- [sdk/rust/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/rust/src/lib.rs)
