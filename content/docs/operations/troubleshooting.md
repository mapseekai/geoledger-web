---
title: "故障诊断"
description: "按启动、登录、版本冲突、容量与发布结果未知定位问题。"
weight: 40
lastmod: 2026-10-29
---

先记录版本、后端、发生时间、业务 code 和 request ID，再检查与症状最接近的分支。日志附件中移除凭据和连接口令，保留能够定位请求的标识。

## 容器未启动或 ready 返回失败

**症状**：Compose 提示会话密钥未设置，或 `GET /ready` 未成功。

**排查**：在源码目录执行 `docker compose ps` 和 `docker compose logs geoledger`，确认构建结束，再检查存储权限、SpatiaLite、已有库格式和端口占用。

**处理**：修正明确配置后重启测试实例，再检查 `/ready`。旧格式使用独立旧程序和旧库恢复，不手动修改格式号。相关值见[配置参考]({{< relref "/docs/reference/configuration/" >}})。

## 控制台能打开但不能登录

**症状**：页面可访问，登录或首次改密失败。

**排查**：核对初始密码文件、用户状态、浏览器实际 origin、BFF 私有 endpoint 和会话密钥。`localhost` 与 `127.0.0.1` 的 origin 不同。

**处理**：按[快速开始]({{< relref "/docs/start/quickstart/" >}})完成首次改密，修正 origin 与服务配置。不要将能打开静态页面作为业务服务就绪的证据。

## 401 或资源不可见

**症状**：API 身份失败，或对已知资源返回 404。

**排查**：检查 Key 是否撤销或过期、用户是否有效、项目成员是否存在，以及工作区是否属于当前用户。资源不可见与不存在可能使用同一返回状态。

**处理**：恢复正确的凭据和成员授权，按[身份指南]({{< relref "/docs/operations/security/" >}})验证权限。待确认发布意图继续保留。

## 保存或发布出现 409

**症状**：工作区版本、HEAD 或冲突选择不匹配。

**排查**：读取工作区和 Conflicts，核对当前编辑版本、HEAD 与字段意图。不要只改 expected_workspace_version 再覆盖提交。

**处理**：按[工作区指南]({{< relref "/docs/guides/workspaces/" >}})重新审阅。字段意图基线失效时按[字段指南]({{< relref "/docs/guides/schema/" >}})重新表达完整意图。

## request_id payload mismatch

**症状**：重试 Publish 时返回该消息。

**原因**：同一个请求 UUID 搭配了不同的原始内容。

**处理**：找回原请求体，用原版本和原说明确认结果。新请求 ID 不能用于确认旧请求，步骤见[发布恢复指南]({{< relref "/docs/guides/publication-recovery/" >}})。

## 413、429 或 504

**症状**：请求大小、执行容量或期限约束触发。

**排查**：先核对请求和响应大小、页大小、并发、数据库锁等待及连接占用，再检查服务日志与指标。

**处理**：根据原因缩小批次或页面、控制并发，或修正数据库等待。发布结果未知时先确认原意图；不对所有写操作使用无条件重试循环。

## PostGIS 连接或纳管失败

**症状**：数据库连接失败，或源表注册被拒绝。

**排查**：依次核对目标库与 TLS、扩展、运行角色、表主键、geometry 声明和业务依赖。配置错误不会回退到 SQLite。

**处理**：由 DBA 修正连接和受限授权，在副本中按[表纳管指南]({{< relref "/docs/guides/postgis/" >}})重做验证，不以扩大所有数据库权限替代定位。

## 实现依据

- [crates/server/src/main.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/main.rs)
- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/publication.rs)
- [docs/security.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/security.md)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
