---
title: "纳管已有 PostGIS 表"
linkTitle: "PostGIS 表纳管"
description: "将符合契约的业务表绑定为数据集，并验证事务写回与历史读取。"
weight: 30
lastmod: 2026-10-29
---

PostGIS 表纳管将已有业务表绑定为 Dataset，正式读取与发布继续使用原表。版本表保留必要的历史和草稿增量。

## 前置条件与影响

先在数据库副本中验证。服务端须配置 PostGIS 后端，操作者具备平台管理能力和目标项目成员身份。

| 检查项 | 要求 |
|---|---|
| 主键 | 单列整数、文本或 UUID 主键 |
| 几何 | 声明类型的 geometry 列，类型、维度与 SRID 符合实际数据 |
| 属性 | 符合纳管契约的普通可写列 |
| 权限 | 满足读写、锁表与保护触发器维护；仅授予 TRIGGER 不足以覆盖全流程 |
| 业务依赖 | 核对已有触发器、约束、列类型和索引 |

注册会建立表绑定、保护触发器和初始版本关系，并检查源数据。它可能产生锁等待与扫描成本，不能当作常量时间的元数据操作。

## 1. 配置数据库与服务

由 DBA 在目标数据库启用 PostGIS 并授予受限服务角色所需权限。按[部署指南]({{< relref "/docs/operations/deployment/" >}})设置 `GL_STORAGE=postgis` 与私有连接字符串，再检查 `/ready`。

服务账号的权限只覆盖需要纳管的表和 GeoLedger 自有对象。连接失败先修正配置，不更换后端以掩盖失败。

## 2. 检查表并建立绑定

在控制台检查可纳管表，提供 schema、表名、主键列和几何列。SDK 入口为 `register_table` / `registerTable` / `RegisterTable`。

HTTP 使用 `create_dataset` 的 `postgis_table` 字段。以下为请求体示意，替换项目占位值，并确认表名来自隔离测试库：

```json
{
  "project": "<project-uuid>",
  "name": "roads",
  "postgis_table": {
    "schema": "public",
    "table": "roads",
    "id_column": "id",
    "geometry_column": "geom"
  }
}
```

注册不会复制每行完整属性与几何。系统复用兼容的 ID 排序索引，必要时建立窄 ID 索引；耗时取决于源数据、索引与锁等待。

## 3. 核对读取与发布

先读取少量要素，核对 ID、属性精度、几何、维度与原始 CRS。创建工作区，只修改一条合成测试要素，审阅后发布。

同时检查原表当前行、发布提交和旧修订。三者应对应同一次事务与版本链路；数据库直查和历史查询承担不同验证职责。

## 4. 检查空间索引

系统不会自动为纳管大表创建空间索引。由表所有者准备 GiST，并使用实际查询计划验证。

```sql
-- 仅为测试表的示例，请先确认实际表名和几何列。
CREATE INDEX roads_geom_gist ON public.roads USING gist (geom);
```

## 后续写入与解除绑定

业务变更通过工作区发布。直接 SQL 写入、替换同名表或修改列结构可能触发保护和漂移检查；纳管能力不提供对任意 SQL 修改的后台 CDC。

删除对应数据集或项目会解除绑定并保留原表，但会清理相应版本数据。操作前保留所需历史备份。原生备份共同覆盖源表、版本表与触发器；逻辑导入恢复为内部数据集，见[备份指南]({{< relref "/docs/operations/backup/" >}})。

## 实现依据

- [crates/engine/src/workspace.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/workspace.rs)
- [crates/engine/src/session/tables.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/engine/src/session/tables.rs)
- [docs/production.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/production.md)
- [docs/storage.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/storage.md)
