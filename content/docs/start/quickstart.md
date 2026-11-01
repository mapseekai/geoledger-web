---
title: "快速开始：启动本地测试环境"
linkTitle: "快速开始"
description: "通过 Docker Compose 从固定源码启动包含服务端、CLI 与 Web 控制台的本地环境，并完成首次登录。"
weight: 20
lastmod: 2026-10-29
---

在本篇教程中，你将使用 Docker Compose 在本地构建并启动一套完整的 GeoLedger 服务（包含 Rust 服务端、SpatiaLite 运行时、命令行工具 `gl` 与 Web 控制台），验证服务就绪状态，并完成管理员首次登录。

完成本教程后，你可以直接进入 **[完成第一次发布]({{< relref "/docs/start/first-publication/" >}})** 体验空间要素的编辑与版本发布。

## 环境准备

开始前，请确认本机已安装 **Git**、**Docker Compose** 与 **OpenSSL**。在终端运行以下命令检查工具版本：

```sh
git --version
docker compose version
openssl version
```

> **提示**：建议在全新的独立目录中执行本教程。如果你之前运行过旧版本的 GeoLedger（存储格式低于 `19`），请使用全新的 Docker 数据卷，详细说明可参考[版本与兼容性]({{< relref "/docs/reference/compatibility/" >}})。

## 步骤 1：获取源码并检出文档基线

克隆 GeoLedger 仓库，并切换到与当前文档完全对应的源码提交：

```sh
git clone https://github.com/mapseekai/geoledger.git
cd geoledger
git checkout 5bf353c88cb017c8c00035fb86667dd2d7497b43
```

固定该提交可以确保你本地运行的服务行为、API 契约与文档中的所有示例完全一致。

## 步骤 2：生成会话密钥并启动容器

Web 控制台需要一个至少 32 字符的随机密钥（`GL_WEB_SESSION_SECRET`）来加密浏览器会话 Cookie。生成该密钥并在后台启动容器：

```sh
export GL_WEB_SESSION_SECRET="$(openssl rand -base64 48)"
docker compose up --build -d
```

首次执行 `--build` 时，Docker 会下载基础镜像并编译 Rust 服务端与前端控制台，通常需要几分钟时间。如果后续需要重启容器并保持已有登录会话有效，请继续沿用同一个 `GL_WEB_SESSION_SECRET`。

## 步骤 3：验证服务就绪状态

容器启动后，使用 `curl` 请求服务端的就绪探针接口 `/ready`：

```sh
curl --fail http://127.0.0.1:7881/ready
```

当服务完成数据库初始化并准备好接收请求时，会返回如下 JSON 响应：

```json
{"ok":true}
```

此时本地环境的三个服务端点均已就绪：

| 服务端点 | 默认本地地址 | 用途说明 |
|---|---|---|
| **Web 控制台** | `http://localhost:3000` | 浏览器可视化管理界面、地图工作台与冲突审阅 |
| **HTTP 业务 API** | `http://127.0.0.1:7881` | 公开 HTTP JSON 接口（`/api/v1/*`）与健康检查探针（`/health`、`/ready`） |
| **gRPC 服务** | `http://127.0.0.1:7882` | 供命令行工具 `gl` 与 Rust / Go / TS / Python SDK 连接 |

> **排查提示**：如果 `/ready` 暂未返回成功，可执行 `docker compose logs -f geoledger` 查看构建与启动进度，或参考[故障诊断]({{< relref "/docs/operations/troubleshooting/" >}})排查端口占用与配置问题。

## 步骤 4：获取初始凭据并完成首次登录

当未通过环境变量显式指定 `GL_ADMIN_PASSWORD` 时，GeoLedger 会在首次启动时自动生成高强度随机管理员密码，并以只读私有权限（`0600`）保存在容器数据卷的 `/data/initial-admin-<id>.json` 文件中。

在终端运行以下命令读取初始管理员凭据：

```sh
docker compose exec geoledger sh -c 'cat /data/initial-admin-*.json'
```

接下来完成首次登录：

1. 在浏览器中打开 `http://localhost:3000`。
2. 输入上述 JSON 文件中的用户名（默认为 `admin`）和随机初始密码进行登录。
3. 按照页面引导**修改初始密码**。密码修改完成后，即可正式进入 GeoLedger 控制台。

> **安全提醒**：初始凭据文件仅用于首次引导登录，请勿将其内容粘贴到公开工单、聊天记录或截图中。后续使用 CLI 或 SDK 时，请在控制台的 **API Key** 页面单独创建个人访问密钥。

## 停止与清理环境

完成后续教程练习后，若需暂停容器但保留已创建的数据卷，可运行：

```sh
docker compose stop
```

## 下一步

服务已经就绪！接下来请继续阅读 **[完成第一次发布]({{< relref "/docs/start/first-publication/" >}})**，亲手创建项目、保存空间要素并体验版本发布与回溯。

## 实现依据

- [compose.yaml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/compose.yaml)
- [Dockerfile](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/Dockerfile)
- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/main.rs)
- [docs/security.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/security.md)
