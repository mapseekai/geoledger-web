---
title: "Web 控制台导览：地图工作台与版本审阅"
linkTitle: "控制台导览"
description: "深入了解 GeoLedger Web 控制台的地图工作台、工作区版本图、历史提交列表与字段变更审阅界面。"
weight: 10
lastmod: 2026-11-01
---

GeoLedger Web 控制台将 GIS 地图浏览、属性检视、工作区草稿管理与版本历史审阅整合在同一套界面中。在进行要素编辑或发布操作前，理解界面中**读取上下文**（已发布修订 vs. 开放工作区草稿）的标识方式至关重要。

## 推荐操作流程

在控制台中开展日常编辑时，建议遵循以下四步习惯：

1. **确认项目与数据集契约**：在左侧导航栏确认当前所选项目与数据集，核对数据集声明的几何类型（点/线/面）、坐标维度（XY/XYZ）及原始坐标系（CRS）。
2. **明确当前数据来源视图**：在数据集工作台顶部工具栏的“数据来源”选择器中，区分当前查看的是**已发布的共享数据**（对应项目 `HEAD`），还是**个人开放工作区**（对应基础修订 `base_revision` 叠加当前草稿增量）。
3. **基于稳定 ID 编辑完整要素**：通过地图拾取、搜索框或底部属性表定位目标要素的稳定字符串 `id`，查看完整 GeoJSON 后修改属性或几何并保存到工作区。
4. **先审阅差异，再执行发布**：切换到“工作区”页面核对变更统计、要素级 Diff 与字段变更，确认无冲突后再填写说明执行发布。

> **初次体验提示**：如果你是第一次使用控制台，建议先跟随 **[完成第一次发布]({{< relref "/docs/start/first-publication/" >}})** 一步步跑通示例。下文展示的界面截图均采集自隔离测试环境中的合成数据集（原图未做裁剪涂改，采集日期与界面版本记录详见[版本与兼容性]({{< relref "/docs/reference/compatibility/" >}})）。

## 1. 地图与属性工作台

{{< screenshot file="console-map.png" alt="GeoLedger PostGIS 地图工作台，展示合成道路测试线与要素属性" >}}

数据集详情页由四个协同区域组成：

- **左侧图层与要素列表**：按点、线、面分组控制显隐，支持按要素 `id`、属性键或属性值实时检索过滤。当数据集要素超过单次加载上限（最多 1,000 条）时，可通过列表底部按钮固定同一修订号继续分页加载。
- **中央地图画布**：默认按几何类型着色（点为橙色、线为蓝色、面为绿色，选中态以黄色高亮），支持离线纯色底图或管理员配置的在线 XYZ 栅格底图。
  - **动态投影预览**：当数据集采用非 WGS 84 坐标系（如 `EPSG:3857` 或地方投影）时，控制台仅在前端利用本地 EPSG 定义与 Proj4js 将显示副本动态转换至 WGS 84 以便在地图上渲染；**底层保存与发布的要素坐标始终严格保持原始 CRS 不变**。
- **右侧要素信息与编辑入口**：未选中要素时展示图层的要素计数、坐标系与空间范围；选中要素后展示完整属性键值、顶点数、包络框，并提供 **缩放至要素**、**编辑** 与 **删除** 操作。
- **底部可折叠属性表**：以表格形式每页展示 100 条要素属性，点击任意行即可与地图画布和左侧列表同步高亮选中。

## 2. 工作区管理与版本演进图

{{< screenshot file="console-workspaces.png" alt="GeoLedger 测试项目的工作区版本图与发布来源" >}}

进入左侧导航栏的 **工作区** 页面后，可在 **版本图** 与 **表格** 两种视图之间自由切换：

- **区分 `rN` 与 `vN`**：界面中的 `rN`（如 `r10`）代表项目级**共享修订号（Revision）**；`vN`（如 `v2`）代表该工作区草稿自身的**乐观编辑版本号（Workspace Version）**。
- **多轨道版本图**：从上到下按时间由旧到新排列已发布修订。连续发布沿主线延伸；当某个工作区基于较早的基础修订（例如 `r1`）完成合并并发布为 `r3` 时，中间的 `r2` 会清晰地展示在支线轨道上。
- **开放草稿节点**：尚未发布的个人工作区显示在提交历史下方，以空心节点和“草稿 / 未提交”标识，清晰标出其当前锚定的 `base_revision`。
- **冲突裁决与变基**：当共享主线 `HEAD` 向前推进导致并发修改冲突时，可在此页面直接打开可视化冲突解决面板，对比“已发布（Current）”与“我的草稿（Draft）”，逐字段或整要素选择保留值并执行 **更新基准（Rebase）**。详见 **[工作区编辑与冲突处理]({{< relref "/docs/guides/workspaces/" >}})**。

## 3. 版本历史与字段定义变更审阅

{{< screenshot file="console-history.png" alt="GeoLedger 测试项目历史列表，展示发布说明和数据集变化" >}}

{{< screenshot file="console-schema.png" alt="GeoLedger alpha.7 发布详情，展示新增 note、删除 gone 与受影响要素" >}}

在 **版本历史** 页面中，你可以追溯项目的每一次演进：

- **按数据集聚合统计**：列表直接展示每次提交在各个数据集上的新增（`added`）、修改（`modified`）与删除（`deleted`）要素计数，无需加载全量 GeoJSON 即可把握变更规模。
- **独立的字段变更视图**：自 `v0.3.0-alpha.7` 起，提交详情与工作区差异均包含独立的 **字段变更（Schema Changes）** 区域，清晰对比发布前后的字段名称与类型（如新增 `note` 字段、移除 `gone` 字段）。因此，在审阅工作区或历史提交时，请同时检查**要素变更**与**字段变更**。
- **一键创建撤销工作区**：历史查看本身是纯只读操作；点击任意历史修订右侧的 **撤销（Restore）**，系统会基于该次提交的反向变更创建一个新的开放工作区，供你审阅后发布为新修订（详见 **[历史查询与撤销]({{< relref "/docs/guides/history/" >}})**）。

## 4. 会话安全与发布确认机制

Web 控制台通过 Next.js BFF（Backend-for-Frontend）与 `geoledger-server` 通信：

- **安全的 Cookie 会话**：浏览器仅持有加密的 `HttpOnly`、`SameSite=Strict` 会话标识，绝不在前端存储明文密码或长期 API Key；真实的身份状态与项目 RBAC 权限由后端数据库实时校验。
- **标签页级发布恢复**：在点击“确认发布”前，控制台会在当前浏览器标签页记录发布意图。若发布期间遇到网络中断或页面超时，可在原标签页重新连接后点击 **重试原发布**。若原事务已提交且调用者仍有权读取，会返回原回执；否则服务端会重新校验或返回错误。详见[发布结果恢复]({{< relref "/docs/guides/publication-recovery/" >}})。

## 实现依据

- [docs/console.md](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/docs/console.md)
- [web/src/components/map-view.tsx](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/web/src/components/map-view.tsx)
- [web/src/components/version-graph.tsx](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/web/src/components/version-graph.tsx)
- [web/src/lib/console-client.ts](https://github.com/mapseekai/geoledger/blob/7bc8b8fac039cfa8f9f659787eeef055fc34ea67/web/src/lib/console-client.ts)
