---
title: "控制台：确认读取与编辑上下文"
linkTitle: "控制台导览"
description: "识别当前项目、数据集、工作区和历史修订，再进入编辑与发布。"
weight: 10
lastmod: 2026-10-29
---

在操作要素前，先确认当前项目、数据集与读取上下文。地图预览、草稿保存和正式发布分别表示不同阶段。

## 操作顺序

1. 选择目标项目与数据集，核对几何声明和原始 CRS。
2. 确认当前读取的是共享修订，还是自己的开放工作区。
3. 通过属性表定位稳定要素 ID，读取完整 Feature 后编辑。
4. 保存后在工作区检查差异，发布后按回执修订读回。

首次练习使用[发布教程]({{< relref "/docs/start/first-publication/" >}})。本页截图来自既有合成数据测试，保留原像素；拍摄日期和可见版本记录在图下，适用边界见[兼容性参考]({{< relref "/docs/reference/compatibility/" >}})。

## 地图与属性工作台

{{< screenshot file="console-map.png" alt="GeoLedger PostGIS 地图工作台，展示合成道路测试线与要素属性" caption="图层、地图与属性呈现同一读取上下文，线为合成测试要素。" >}}

地图预览可按需转换坐标，不改变保存的原始坐标。属性表用于定位和核对字段；GeoJSON 编辑入口提交完整要素。

新增与修改先保存到工作区。核对工作区版本和差异后，再按[编辑与审阅指南]({{< relref "/docs/guides/workspaces/" >}})发布。

## 工作区与版本图

{{< screenshot file="console-workspaces.png" alt="GeoLedger 测试项目的工作区版本图与发布来源" caption="版本图展示工作区基线和实际发布来源。" >}}

核对基础修订、草稿编辑版本和来源工作区。版本图描述数据版本关系，工作区的开放读取状态为固定基线叠加自己的增量。

HEAD 推进后重新检查冲突与解决上下文。旧选择失效时，读取最新 Base、Current 和 Draft 后重新审阅。

## 提交与字段变化

{{< screenshot file="console-history.png" alt="GeoLedger 测试项目历史列表，展示发布说明和数据集变化" caption="提交详情用于核对实际发布的要素与版本关系。" >}}

{{< screenshot file="console-schema.png" alt="GeoLedger alpha.7 发布详情，展示新增 note、删除 gone 与受影响要素" caption="字段变化独立展示；纯字段变更也属于一次发布。" >}}

历史查看是只读操作；Restore 创建新的反向工作区，步骤见[历史指南]({{< relref "/docs/guides/history/" >}})。审阅提交时同时检查要素与字段，不能仅凭要素计数判断提交是否为空。

## 结果确认

浏览器经 Next.js BFF 调用服务，身份和权限由业务服务验证。界面中的草稿变化不代表共享修订已经推进；以成功回执和固定修订读回确认结果。

发布响应中断时使用[恢复指南]({{< relref "/docs/guides/publication-recovery/" >}})，保留原发布意图。

## 实现依据

- [docs/console.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/console.md)
- [web/src/components/map-view.tsx](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/web/src/components/map-view.tsx)
- [web/src/components/version-graph.tsx](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/web/src/components/version-graph.tsx)
- [web/src/lib/console-client.ts](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/web/src/lib/console-client.ts)
