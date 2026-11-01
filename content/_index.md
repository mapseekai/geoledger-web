---
title: GeoLedger · 空间数据，版本有据
description: 为每一次空间数据更新建立明确的版本边界。支持独立工作区、要素级差异审阅、属性级三方合并与事务化原子发布，兼容 PostgreSQL + PostGIS 与 SQLite + SpatiaLite。
body_class: gl-home
---
GeoLedger 是基于 Rust 构建的开源空间要素版本管理与协作编辑服务。团队成员可以在各自独立的工作区（Workspace）中编辑 GeoJSON 要素与字段定义，通过差异审阅（Diff）和三方合并（Three-Way Merge）解决并发冲突，并在单个数据库事务中发布为项目级共享修订（Revision）。支持 SQLite + SpatiaLite 与 PostgreSQL + PostGIS 双存储后端，并提供 Web 控制台、CLI、HTTP API 以及 Rust、Go、TypeScript / Node.js、Python 四语言 SDK。

从[快速开始](docs/start/quickstart/)启动你的第一个服务实例，深入了解[整体架构](docs/architecture/overview/)，或浏览[版本变更记录](blog/)。
