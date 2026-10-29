---
title: "部署与运行"
description: "配置服务、存储、私有控制台传输与网关，再验证完整发布链路。"
weight: 10
lastmod: 2026-10-29
---

部署前固定源码或镜像 digest，明确数据持久化和网络边界。先在独立环境验证登录、保存、发布与恢复，再将相同配置交付目标环境。

## 前置条件与部署选择

首次搭建先完成[快速开始]({{< relref "/docs/start/quickstart/" >}})。升级或复用数据库前核对[存储兼容性]({{< relref "/docs/reference/compatibility/" >}})，保留独立备份与旧环境恢复路径。

| 方式 | 适用情况 | 准备内容 |
|---|---|---|
| 统一容器 | 将服务、CLI、控制台与原生依赖一起运行 | 持久化卷、会话密钥、网关与探针 |
| 原生二进制 | 由现有 systemd 或进程管理部署 | Rust 构建环境、SpatiaLite 运行依赖、独立控制台 |
| PostGIS 生产模板 | 需要数据库角色隔离与已有表纳管 | DBA 配置、TLS、原表权限与数据库备份 |

统一镜像以非 root 用户运行，包含 Next.js standalone 控制台与 SpatiaLite 依赖。原生服务构建命令为 `cargo build --release --locked --bins`，生成的服务与 CLI 位于 `target/release/`。

## 1. 准备持久化与身份

SQLite 模式持久化数据目录；PostGIS 模式明确目标数据库，并保留服务端数据目录中的私有初始化文件。为控制台配置稳定的随机会话密钥。

首次登录完成改密，再为客户端创建独立个人 Key。用户和项目角色的配置见[身份与安全]({{< relref "/docs/operations/security/" >}})。所有配置键及默认值由[配置参考]({{< relref "/docs/reference/configuration/" >}})维护。

## 2. 配置数据库连接

使用 PostGIS 时，由 DBA 在专用数据库启用扩展并配置受限运行角色。服务进程显式设置后端与私有连接字符串，例如：

```sh
export GL_STORAGE=postgis
# 示例目标；真实连接与密码由私有环境配置提供。
export GL_DATABASE_URL='postgresql://geoledger@db.internal:5432/geoledger?sslmode=verify-full'
```

私有 CA 通过 sslrootcert 提供。账号须有初始化和所选业务表操作的实际权限；已有数据库的授权由 DBA 审核，Compose 的新卷初始化脚本不会修复旧卷角色配置。

## 3. 配置控制台与网关

分别设置 BFF 的私有 `GL_WEB_ENDPOINT` 与浏览器真实 `GL_WEB_ORIGIN`。外部域名、端口和 HTTPS 改变后，origin 也须保持一致。

公开访问使用 HTTPS，明确控制台、HTTP API 和 gRPC 各自路由。仓库的 Nginx、Caddy 与 Compose 配置作为部署起点；只在可信网关确实设置来源头时开启 forwarded-for 信任。

## 4. 检查健康与业务链路

| 检查 | 观察结果 |
|---|---|
| GET /health | 进程存活与版本信息 |
| GET /ready | 接单状态、容量与存储就绪 |
| GET /metrics | 携带 Bearer 身份的 Prometheus 指标 |
| 控制台首次登录 | 完成改密并建立数据库 Session |
| 测试工作区 | 保存、审阅、发布、按回执修订读回 |
| 发布确认 | 重放原请求返回同一发布结果 |
| 隔离恢复 | 恢复后的历史、身份和发布链路可用 |

记录实际运行版本、目标机器、后端和失败步骤。容量参数根据数据库等待、连接占用与实际编码大小调整，不将默认值当作目标吞吐量。

## 停止、回退与恢复

先使服务进入排空状态，再关闭监听并等待在途请求和数据库清理。客户端响应中断后仍须确认待定发布，见[恢复指南]({{< relref "/docs/guides/publication-recovery/" >}})。

配置错误时恢复已保存的配置并重新检查就绪。数据库格式变更的回退使用旧程序和独立旧库，不能让旧程序直接读取新格式库。故障数据恢复按[备份指南]({{< relref "/docs/operations/backup/" >}})执行。

## 实现依据

- [compose.yaml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/compose.yaml)
- [Dockerfile](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/Dockerfile)
- [deploy/compose.production.yaml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/deploy/compose.production.yaml)
- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/main.rs)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
