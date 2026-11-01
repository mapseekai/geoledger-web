---
title: "性能基准与容量规划参考"
linkTitle: "性能与容量规划"
description: "查阅历史性能测试结果、测量条件与容量规划方法，并在自己的环境中复现基准。"
weight: 70
lastmod: 2026-10-31
---

本文汇总源码仓库保留的历史性能测试结果，并说明如何在目标环境中测量容量。

下列数据来自 2026-10-11 的格式 13 测试：PostGIS 使用 `v0.3.0-alpha.2` 候选构建，SQLite 使用同日上一候选构建。当前固定源码使用存储格式 19，因此这些结果不能代表当前版本或生产容量。完整条件与报告见[源码性能测试说明](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/performance.md)。

---

## 历史基准：48 万条要素

### 1. 测试环境与夹具

- **测试硬件**：Apple Silicon 10 核 CPU，16 GiB 统一内存。
- **存储后端**：
  - **PostGIS**：Docker 容器运行 PostgreSQL 17 + PostGIS 3.6。
  - **SQLite**：本机编译版本，加载 `GL_SPATIALITE_EXTENSION` 扩展。
- **背景夹具**：**483,268 条真实三维（XYZ）空间线要素**，原始数据体积约 **999 MiB**。
- **构建模式**：Release 优化构建（`--locked --release`）。
- **运行条件**：测试机同时运行其他开发服务；结果只代表该机器、数据和当次运行。

### 2. 大数据集增量增删改延迟

在已加载 483,268 条空间线要素的数据库上，执行 10、100、500 条要素的增删改循环。每组 20 轮，500 条保存拆分为 5 次 RPC 后发布。下表按增删改汇总，每种批量有 100 个样本；时间包含保存和首次发布，重放与回读另记。RSS 是整个测试过程中服务进程的峰值，并非各批次的独立测量。

| 存储后端 | 批量大小 | p95 延迟（ms） | p99 延迟（ms） | 最大延迟（ms） | 内存 RSS 峰值 |
|---|---:|---:|---:|---:|---:|
| **SQLite / SpatiaLite** | 10 条 | 52 | 78 | 210 | 103.64 MiB |
| **SQLite / SpatiaLite** | 100 条 | 199 | 311 | 560 | 103.64 MiB |
| **SQLite / SpatiaLite** | 500 条 | 1,348 | 4,106 | 4,217 | 103.64 MiB |
| **PostGIS (0.3.0-alpha.2)** | 10 条 | 111 | 201 | 545 | 30.81 MiB |
| **PostGIS (0.3.0-alpha.2)** | 100 条 | 598 | 1,115 | 1,918 | 30.81 MiB |
| **PostGIS (0.3.0-alpha.2)** | 500 条 | 4,939 | 8,018 | 8,081 | 30.81 MiB |

这组数字不包含实际业务环境的额外索引、触发器或网络开销。

### 3. 20 路并发读写与发布

在 PostGIS 后端上施加 **20 路并发持续 300 秒** 压力测试，累计完成 404 个完整增删改循环、1,212 次首次发布与 1,212 次收据重放，**服务端错误数为 0**：

| 操作类型 | 说明与批量规模 | p95 延迟（ms） | p99 延迟（ms） |
|---|---|---:|---:|
| **单次保存（Save）** | 最多 100 条空间要素 | 492 | 889 |
| **首次发布（Publish）** | 获取全局排他写锁，生成新修订 | 5,916 | 9,824 |
| **收据重放（Idempotent Publish）** | 使用原 `request_id` 重放发布请求 | 22 | 48 |
| **单要素回读（Point Query）** | 按要素 ID 查询 | 24 | 53 |

**本次性能验收未通过，需在空闲环境复测。** 500 条新增、修改、删除的首次发布分组 p95 分别为 6,415、8,731、8,961 ms，超过每组 5,000 ms 的门限；部分较小批量也超出门限。测试期间宿主机持续大量换页，不能据此确定稳定容量。服务进程 RSS 峰值为 55.61 MiB，原生内存扫描因调试权限受限记为 `error`。

---

## 服务端资源与执行限制（Limits）

并发数、请求期限、收发字节预算和可选速率限制的变量及默认值见[配置参数参考]({{< relref "/docs/reference/configuration/" >}})。这些预算不等于进程总内存；容量规划还应测量数据库连接、几何对象和其他运行开销。

---

## 生产容量规划指南

### 1. 存储空间容量预估

估算空间时，除了当前要素，还应考虑被修改或删除要素的历史正文、开放工作区草稿、索引、数据库日志和备份。各部分增长取决于几何与属性大小、变更频率、工作区数量和数据库配置，应使用实际数据测量，不能套用固定倍率。

### 2. 空间查询与 GiST 索引维护

针对 PostGIS 业务表，检查现有几何列索引与查询计划，并结合业务索引、约束和触发器测量导入与发布开销。索引维护操作应遵循该数据库的运行规程。

### 3. 固定修订读取

分页读取时可固定首次返回的 `revision`，使各页查询同一共享修订。读取与写入吞吐仍需在目标部署环境中单独测量，详见[分页与一致性参考]({{< relref "/docs/reference/pagination/" >}})。

---

## 本地基准测试复现指南

在隔离环境中使用源码仓库的性能测试脚本，记录构建摘要、数据集、硬件、网络及持续负载条件。脚本创建独立测试服务和数据库；请使用新的输出目录，不要指向生产数据。

### 1. 增量增删改基准测试

```sh
# 1. 编译 release 构建的服务端与基准测试工具
cargo build --locked --release -p geoledger-server -p geoledger-client \
  --bin geoledger-server --example incremental --example fixture_jsonl

# 2. 根据源数据的实际坐标系生成测试输入
mkdir -p artifacts/performance/fixtures
target/release/examples/fixture_jsonl /path/to/buildings.geojson \
  artifacts/performance/fixtures/buildings.jsonl EPSG:4326 \
  > artifacts/performance/fixtures/buildings.meta.json

# 3. 运行 10 轮增量读写基准测试
python3 scripts/benchmark_incremental.py \
  --server target/release/geoledger-server \
  --client target/release/examples/incremental \
  --fixture artifacts/performance/fixtures/buildings.jsonl \
  --metadata artifacts/performance/fixtures/buildings.meta.json \
  --output artifacts/performance/incremental-run \
  --rounds 10
```

### 2. k6 HTTP 压力测试

```sh
# 结合 k6 运行 5 / 20 / 50 req/s 固定到达率压测
python3 scripts/benchmark.py \
  --geojson /path/to/buildings.geojson \
  --output artifacts/performance/http-run \
  --k6 /usr/local/bin/k6
```

## 实现依据

- [docs/performance.md](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/docs/performance.md)
- [crates/server/src/limits.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/limits.rs)
- [scripts/benchmark_incremental.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/scripts/benchmark_incremental.py)
- [crates/server/src/http.rs](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/crates/server/src/http.rs)
