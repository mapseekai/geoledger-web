---
title: "快速开始：启动测试环境"
linkTitle: "快速开始"
description: "从固定源码构建统一容器，检查就绪状态并完成首次登录。"
weight: 20
lastmod: 2026-10-29
---

完成后，你将得到可登录的控制台和通过就绪检查的业务服务。接下来用[第一次发布]({{< relref "/docs/start/first-publication/" >}})验证保存、发布与读取。

## 前置条件

准备 Git、Docker Compose 和 OpenSSL，在一个独立测试目录操作。先确认命令可用：

```sh
git --version
docker compose version
openssl version
```

使用新的 Docker 数据卷。已有实例或旧格式数据库的处理方式见[版本兼容性]({{< relref "/docs/reference/compatibility/" >}})。以下命令会构建容器并创建测试数据目录。

## 1. 获取文档对应的源码

```sh
git clone https://github.com/mapseekai/geoledger.git
cd geoledger
git checkout 5bf353c88cb017c8c00035fb86667dd2d7497b43
```

该提交是本站的实现依据，包含 alpha.7 标签之后的主分支变更。需要复现发布包时，使用[兼容性参考]({{< relref "/docs/reference/compatibility/" >}})中的发布基线，不混用两套源码。

## 2. 启动容器

```sh
export GL_WEB_SESSION_SECRET="$(openssl rand -base64 48)"
docker compose up --build -d
```

将会话密钥保存在私有配置中，以便重启时复用。首次构建会下载依赖并编译；不要在构建结束前判断服务失败。

## 3. 检查服务就绪

```sh
curl --fail http://127.0.0.1:7881/ready
```

预期响应为 `{"ok":true}`。`/health` 用于检查进程存活，`/ready` 还检查接单状态与存储。失败时先执行 `docker compose logs geoledger`，按[故障诊断]({{< relref "/docs/operations/troubleshooting/" >}})区分启动、数据库与容量问题。

| 入口 | 默认地址 | 使用者 |
|---|---|---|
| 控制台 | `http://localhost:3000` | 浏览器 |
| HTTP API | `http://127.0.0.1:7881` | HTTP 客户端与控制台 BFF |
| gRPC | `http://127.0.0.1:7882` | CLI 与四语言 SDK |

这些是本机测试地址。对外部署的监听、TLS 和网关配置见[部署与运行]({{< relref "/docs/operations/deployment/" >}})。

## 4. 完成首次登录

未设置初始化密码时，服务端生成随机密码并保存为私有文件。在自己的终端读取：

```sh
docker compose exec geoledger sh -c 'cat /data/initial-admin-*.json'
```

打开控制台，用文件中的用户名与密码登录，再按提示修改初始密码。不要将文件内容放入工单、日志附件或截图。程序接入所需的个人 API Key 在登录后单独创建。

## 结果验证与停止

确认 `/ready` 成功、首次改密完成，并能进入控制台。继续[创建工作区并发布一个要素]({{< relref "/docs/start/first-publication/" >}})，完成业务链路验证。

结束测试时运行：

```sh
docker compose stop
```

该命令停止容器并保留数据卷。重新启动时使用原会话密钥；重建旧版本环境时使用与其匹配的数据库和程序。

## 实现依据

- [compose.yaml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/compose.yaml)
- [Dockerfile](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/Dockerfile)
- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/main.rs)
- [docs/security.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/security.md)
