---
title: "版本、兼容性与验证范围"
linkTitle: "版本与兼容性"
description: "查阅当前文档对应的 GeoLedger 源码基线、发布标签、存储格式版本（Format 19）与客户端协议兼容性边界。"
weight: 5
lastmod: 2026-11-01
---

为了确保技术文档中的每一个命令、API 字段和配置参数都准确可复现，本站所有内容均严格绑定于固定的 GeoLedger 源码提交基线进行编写与核对。

## 当前文档版本矩阵

| 维度 | 当前基线值 | 说明与用途 |
|---|---|---|
| **文档源码基线（Commit SHA）** | `7bc8b8fac039cfa8f9f659787eeef055fc34ea67` | 本站教程、API 契约与源码引用锚定的精确提交（核对日期：2026-11-01） |
| **源码版本标识（Version）** | `0.3.0-alpha.9` | Rust 工作区及服务端 `/health` 使用此标识；Python 包元数据使用 PEP 440 格式 `0.3.0a9` |
| **发布标签** | [`v0.3.0-alpha.9`](https://github.com/mapseekai/geoledger/releases/tag/v0.3.0-alpha.9)（提交 `7bc8b8fac039cfa8f9f659787eeef055fc34ea67`） | 与文档源码基线一致；包含数据来源选择器版本同步修复。镜像为 `docker.io/zwishing/geoledger:0.3.0-alpha.9`（[Docker Hub](https://hub.docker.com/r/zwishing/geoledger/tags)） |
| **镜像清单摘要** | `sha256:3fdf1371c3a1ecf8f4989c5de52cbb3dceec5807ecd8b6069dc0905b0cf0afcd` | 双架构镜像清单摘要；可使用 `docker.io/zwishing/geoledger@sha256:3fdf1371c3a1ecf8f4989c5de52cbb3dceec5807ecd8b6069dc0905b0cf0afcd` 固定镜像 |
| **存储格式版本（Storage Format）** | `19` | 服务端启动及备份恢复时强制校验的数据库结构版本号（定义于 `crates/engine/src/lib.rs`） |
| **业务通信协议** | gRPC `geoledger.v1` · HTTP `/api/v1` | 客户端 SDK、CLI 与外部 HTTP 集成使用的统一协议版本 |

> **复现本站版本**：`v0.3.0-alpha.9` 指向上述固定提交。请按照 **[快速开始]({{< relref "/docs/start/quickstart/" >}})** 检出该提交并从源码构建，或使用对应的已发布容器镜像。

## 客户端与服务端配套要求

1. **同版本部署原则**：`geoledger-server`、远程命令行工具 `gl`、Web 控制台以及四语言 SDK（Rust、Go、TypeScript / Node.js、Python）应使用同一源码提交或同一次 Release 构建的配套产物。
2. **源码安装方式**：本站教程与参考示例均直接从检出的 GeoLedger 源码目录（`./sdk/rust`、`./sdk/go`、`./sdk/ts`、`./sdk/python`）构建或安装客户端，不依赖外部公共包注册表（如 PyPI、npm）是否已同步上传该预发布版本。
3. **跨传输协议表示差异**：虽然 HTTP `/api/v1`、gRPC `geoledger.v1` 与 Web 控制台内部调用共享同一个领域引擎，但它们在 64 位大整数、可选空值与分页终页信号上的表示形式各有约定，请对照 **[SDK 参考]({{< relref "/docs/reference/sdk/" >}})**、**[HTTP 参考]({{< relref "/docs/reference/http/" >}})** 与 **[分页参考]({{< relref "/docs/reference/pagination/" >}})** 处理。

## 存储格式 `19` 与升级规范

- **不支持旧格式原地直接升级**：`v0.3.0-alpha.7` 引入了按数据集独立分表与版本化字段定义，存储格式由 `16`（及过渡态 `18`）升级为 **`19`**。当前版本服务启动时会自动将全新的空目录或空库初始化为格式 `19`，并**明确拒绝挂载旧格式的数据库文件或导入旧格式的逻辑导出**。
- **平滑迁移建议**：
  - 切勿手动修改数据库内部的格式版本号，也不要让不同版本的 `geoledger-server` 共享同一个数据库。
  - 从旧格式升级时，请完整保留旧版二进制程序、旧格式数据库与独立备份；为新版本准备全新的数据目录或空数据库，并在隔离环境中验证迁移与恢复流程（见 **[备份、导出与恢复]({{< relref "/docs/operations/backup/" >}})**）。从格式 19 升级时可继续使用原数据库，仍应先备份并停止旧服务。

## 文档验证范围与界面截图说明

- **源码级契约核对**：本站每一篇技术文档末尾均附有 **实现依据**，直接链接至固定提交 `7bc8b8f` 中的源码文件或协议定义。
- **真实测试环境截图**：控制台导览与首页中展示的界面截图均采集自运行真实 PostGIS / SQLite 后端的隔离测试环境（使用合成演示数据，未经任何像素涂改）。采集日期、界面版本、资产哈希与来源记录在站点仓库的 `data/screenshots.json` 中。

## 实现依据

- [Cargo.toml](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/Cargo.toml)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/crates/engine/src/lib.rs)
- [proto/geoledger/v1/geoledger.proto](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/proto/geoledger/v1/geoledger.proto)
- [CHANGELOG.md](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/CHANGELOG.md)
