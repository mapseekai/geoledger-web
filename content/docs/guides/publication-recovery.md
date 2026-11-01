---
title: "确认与恢复中断的发布（幂等重试）"
linkTitle: "发布结果恢复"
description: "当发布请求遭遇网络超时、连接中断或客户端进程重启时，利用不可变发布意图（request_id）安全确认结果，杜绝重复发布。"
weight: 60
lastmod: 2026-11-01
---

在分布式系统与网络通信中，客户端调用 `publish` 时可能会遇到连接闪断、网关 `504 Gateway Timeout` 或客户端进程意外重启。此时，**服务端数据库事务可能已经成功提交，也可能在提交前已回滚**。

如果客户端简单地创建一个新工作区重新提交，就可能导致同一批变更被重复发布两次。GeoLedger 在数据库事务内保存**不可变发布回执**（Publication Receipt）：使用同一身份和原始发布意图重放时，若原事务已提交且调用者仍有权读取，服务端返回原回执；若尚未提交，服务端会重新校验并尝试执行。保留原意图可避免因重试本身生成重复修订。

## 核心要素：一份发布意图包含什么？

在发起发布请求前，客户端（或 SDK 工作区句柄）会固定以下五个要素：

| 字段名称 | 作用说明 | 重试时的严格要求 |
|---|---|---|
| `project` / `workspace` | 标识目标项目与待发布的工作区 UUID | 保持原资源 ID |
| `request_id` | 唯一标识本次发布意图的 UUID | **必须沿用首次生成的同一个 UUID** |
| `expected_workspace_version` | 发起发布时该工作区的乐观编辑版本号 | **必须保持原版本号**（不要先刷新再改为新版本号） |
| `message` | 本次发布的版本说明文本 | **必须保持原说明文本一字不差** |
| 调用者身份（`subject`） | 由 API Key 或控制台 Session 解析出的用户 UUID | 回执按 `(project, subject, request_id)` 唯一索引 |

> **操作铁律**：当一次发布调用的结果处于“未知（Uncertain）”状态时，**请先暂停对该工作区发起任何新的 `save`、`resolve` 或新的发布意图**，先按本指南完成原请求的确认。

## 步骤 1：区分“明确拒绝”与“结果未知（Uncertain）”

捕获到发布异常时，首先检查错误类型：

- **明确拒绝（`uncertain = false`）**：首次调用直接收到 `400/422`（参数非法）或 `409 Conflict`（例如合并冲突）时，该次请求未提交；可以修正问题后再发起发布。若此前已有结果未知的尝试，后续认证或权限错误不能证明原请求的结果，仍需保留原意图。
- **结果未知（`uncertain = true`）**：例如网络断连、请求超时（`504` / `deadline_exceeded`）或服务暂时不可用（`503` / `unavailable`）。此时 SDK 错误对象的 `uncertain`（Go 为 `Uncertain`）属性为 `true`，必须进入下方的决策与恢复流程。

### 发布故障恢复决策流程图

{{< publication-recovery-flow >}}

## 步骤 2：在未重启的同一进程内直接重试

如果应用仍保留原工作区句柄，或控制台原标签页仍保存发布意图，可以直接重试：

- **使用四语言 SDK**：SDK 的 `Workspace` 句柄在内部自动缓存了未确认的 `request_id`、`expected_workspace_version` 和 `message`。你只需**在同一个工作区句柄上，传入完全相同的发布说明再次调用 `publish`**：

**Python 示例**：
```python
from geoledger import GeoLedgerError

try:
    receipt = draft.publish("新增示例监测点")
except GeoLedgerError as err:
    if err.uncertain:
        # 使用同一句柄与完全相同的 message 重试，底层自动复用原 request_id
        receipt = draft.publish("新增示例监测点")
    else:
        raise
```

**Go 示例**：
```go
// appCtx 是仍有效的应用生命周期 context，不从可能超时的 ctx 派生。
receipt, err := draft.Publish(ctx, "新增示例监测点")
if err != nil {
    var geoErr *geoledger.Error
    if errors.As(err, &geoErr) && geoErr.Uncertain {
        // 为确认请求设置新的期限，继续使用原句柄与相同说明。
        retryCtx, cancel := context.WithTimeout(appCtx, 30*time.Second)
        receipt, err = draft.Publish(retryCtx, "新增示例监测点")
        cancel()
    }
    if err != nil {
        return fmt.Errorf("发布确认失败: %w", err)
    }
}
```

- **使用Web 控制台**：重新连接或重新登录后，进入 **工作区** 页面，点击顶部提示的 **重试原发布** 按钮即可。
- **使用 HTTP API 或 CLI**：将首次保存的原始 JSON 请求体原封不动地重新 POST 到 `/api/v1/publish`（或再次执行 `gl call publish --file publish-req.json`）。

> **为什么会遇到 `request_id payload mismatch`？**
> 如果你在重试时保留了原 `request_id`，却修改了 `message` 文案或 `expected_workspace_version`，服务端会检测到同一 `request_id` 携带了矛盾的请求负载，并返回 `409 Conflict (request_id payload mismatch)`。此时只需找回首次发送的原始 `expected_workspace_version` 和 `message` 重新提交即可。

## 步骤 3：跨进程重启后的持久化恢复

工作区句柄在首次调用 `publish` 时创建发布意图，因此第一次调用之前，其 `pending_publication` 为空。收到结果未知的错误后，可以从仍存活的句柄读取意图并持久化：

| 语言 SDK | 获取待确认意图的方法 / 属性 | 序列化与反序列化恢复方式 |
|---|---|---|
| **Python** | `draft.pending_publication` | 用 `dataclasses.asdict()` 存为 JSON；恢复时构造 `Publication(**data)` 并调用 `client.publish(intent)` |
| **Rust** | `draft.pending_publication()` | 使用 `serde_json` 序列化 `Publication`；恢复后调用 `client.publish(&intent).await?` |
| **Go** | `draft.PendingPublication()` | 使用 `encoding/json` 序列化 `*geoledger.Publication`；恢复为 `geoledger.Publication` 后调用 `client.Publish(ctx, intent)` |
| **TypeScript** | `draft.pendingPublication` | 使用 SDK 提供的 `stringifyJson` 保存；恢复时用 `parseJson` 读取并将 `expectedWorkspaceVersion` 还原为 `BigInt(val)`，再调用 `await client.publish(intent)` |

如果还要覆盖首次请求在途时进程突然退出的情况，应用需要在发送前自行构造完整的 `Publication` 意图并可靠持久化，再调用 `client.publish(intent)`；在记录预期工作区版本和发送请求之间，避免其他操作修改该工作区。仅在捕获错误后保存句柄意图无法覆盖进程在收到错误前退出的情况。

当新进程启动后，直接通过 `client.publish(intent)` 提交还原后的意图：
- **若原事务当时已提交**：服务端从 `gl_idempotency` 表中查出原回执并返回。即使项目已归档或发布者角色已降为 `viewer`，只要回执和工作区仍存在、调用者仍是有效成员且工作区归属未变，仍允许重放读取。
- **若原事务当时未提交（已回滚）**：服务端会使用原意图重新尝试发布，并重新检查权限、工作区版本和合并条件；若这些条件不再满足，可能返回明确错误而不是回执。

## 步骤 4：核对最终结果与特殊情况处理

1. **验证发布回执**：拿到返回的 `receipt` 后，核对 `revision`、`workspace` 与 `status == "published"`，并可按该 `revision` 读取要素或查看 `history`。
2. **重试期间遇到 `401` / `403` / `404` 怎么办？**
   - 如果在重试时恰好遇到 API Key 过期、会话失效或权限暂时变更，SDK **不会清除**已保存的 `pending_publication` 意图。请先由管理员恢复有效凭据或成员权限，然后继续使用原意图完成确认，切勿因此丢弃原意图。
3. **原始意图意外丢失后的人工核查**：
   - 如果客户端既未收到响应，又因未做持久化而丢失了原 `request_id`，请勿盲目新建请求。操作人员可在控制台或通过 API 检查工作区状态，并分页查看项目 `history` 中对应 `source_workspace` 的提交；期间其他工作区可能已经产生更新的修订。

## 实现依据

- [crates/engine/src/publication.rs](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/crates/engine/src/publication.rs)
- [sdk/python/geoledger/__init__.py](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/sdk/python/geoledger/__init__.py)
- [sdk/ts/src/index.ts](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/sdk/ts/src/index.ts)
- [docs/api.md](https://github.com/mapseekai/geoledger/blob/9d31fb5f1e3547ba940518564105cb4a13ea42df/docs/api.md)
