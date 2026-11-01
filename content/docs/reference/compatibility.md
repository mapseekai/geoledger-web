---
title: "版本、兼容性与验证范围"
linkTitle: "版本与兼容性"
description: "查阅当前文档对应的 GeoLedger 源码基线、发布标签、存储格式版本（Format 19）与客户端协议兼容性边界。"
weight: 5
lastmod: 2026-10-29
---

为了确保技术文档中的每一个命令、API 字段和配置参数都准确可复现，本站所有内容均严格绑定于固定的 GeoLedger 源码提交基线进行编写与核对。

## 当前文档版本矩阵

| 维度 | 当前基线值 | 说明与用途 |
|---|---|---|
| **文档源码基线（Commit SHA）** | `5bf353c88cb017c8c00035fb86667dd2d7497b43` | 本站所有教程、API 契约与源码引用链接所锚定的精确提交（核对日期：2026-10-29） |
| **源码版本标识（Version）** | `0.3.0-alpha.7` | `Cargo.toml`、服务端 `/health` 响应及四语言 SDK 报告的版本字符串 |
| **最近正式发布标签（Release Tag）** | `v0.3.0-alpha.7`（提交 `f0109c8ff424dc974421072cb2ff9b366f12c17a`） | 2026-10-26 发布的正式版本标签；源码基线 `5bf353c` 包含了该标签之后的几项主分支工程优化与依赖修复 |
| **存储格式版本（Storage Format）** | `19` | 服务端启动及备份恢复时强制校验的数据库结构版本号（定义于 `crates/engine/src/lib.rs`） |
| **业务通信协议** | gRPC `geoledger.v1` · HTTP `/api/v1` | 客户端 SDK、CLI 与外部 HTTP 集成使用的统一协议版本 |

> **如何区分 Release 标签与主分支基线？**
> 在 `0.x` 预发布阶段，主分支在两次正式打标之间仍会合入工程改进，而 `Cargo.toml` 中的版本号可能暂未递增。因此，复现本站在 **[快速开始]({{< relref "/docs/start/quickstart/" >}})** 中的教程时，请直接 `git checkout 5bf353c88cb017c8c00035fb86667dd2d7497b43`；若需了解正式发布标签与主分支提交之间的具体差异，请分别参阅 **[alpha.7 发布说明]({{< relref "/blog/alpha-7/" >}})** 与 **[主分支工程记录]({{< relref "/blog/main-2026-10-29/" >}})**。

## 客户端与服务端配套要求

1. **同版本部署原则**：`geoledger-server`、远程命令行工具 `gl`、Web 控制台以及四语言 SDK（Rust、Go、TypeScript / Node.js、Python）应使用同一源码提交或同一次 Release 构建的配套产物。
2. **源码安装方式**：本站教程与参考示例均直接从检出的 GeoLedger 源码目录（`./sdk/rust`、`./sdk/go`、`./sdk/ts`、`./sdk/python`）构建或安装客户端，不依赖外部公共包注册表（如 PyPI、npm）是否已同步上传该预发布版本。
3. **跨传输协议表示差异**：虽然 HTTP `/api/v1`、gRPC `geoledger.v1` 与 Web 控制台内部调用共享同一个领域引擎，但它们在 64 位大整数、可选空值与分页终页信号上的表示形式各有约定，请对照 **[SDK 参考]({{< relref "/docs/reference/sdk/" >}})**、**[HTTP 参考]({{< relref "/docs/reference/http/" >}})** 与 **[分页参考]({{< relref "/docs/reference/pagination/" >}})** 处理。

## 存储格式 `19` 与升级规范

- **不支持旧格式原地直接升级**：`v0.3.0-alpha.7` 引入了按数据集独立分表与版本化字段定义，存储格式由 `16`（及过渡态 `18`）升级为 **`19`**。当前版本服务启动时会自动将全新的空目录或空库初始化为格式 `19`，并**明确拒绝挂载旧格式的数据库文件或导入旧格式的逻辑导出**。
- **平滑迁移建议**：
  - 切勿手动修改数据库内部的格式版本号，也不要让不同版本的 `geoledger-server` 共享同一个数据库。
  - 升级已有环境时，请完整保留旧版二进制程序、旧格式数据库与独立备份；为新版本准备全新的数据目录或空数据库，并在隔离环境中验证业务要素迁移与恢复流程（同格式备份与跨后端逻辑导入详见 **[备份、导出与恢复]({{< relref "/docs/operations/backup/" >}})**）。

## 文档验证范围与界面截图说明

- **源码级契约核对**：本站每一篇技术文档末尾均附有 **实现依据**，直接链接至固定提交 `5bf353c` 中的源码文件或协议定义。
- **真实测试环境截图**：控制台导览与首页中展示的界面截图均采集自运行真实 PostGIS / SQLite 后端的隔离测试环境（使用合成演示数据，未经任何像素涂改）。采集日期、界面版本、资产哈希与来源记录在站点仓库的 `data/screenshots.json` 中。

## 实现依据

- [Cargo.toml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/Cargo.toml)
- [crates/engine/src/lib.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/lib.rs)
- [proto/geoledger/v1/geoledger.proto](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/proto/geoledger/v1/geoledger.proto)
- [CHANGELOG.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/CHANGELOG.md)
