---
title: "教程：用 Python 发布并读回要素"
linkTitle: "Python SDK 教程"
description: "从源码安装客户端，创建工作区并按发布回执读取一个合成监测点。"
weight: 40
lastmod: 2026-10-29
---

本教程通过 Python SDK 完成创建项目、保存草稿、发布和固定修订读取。示例会向测试服务写入数据。

## 前置条件

完成[快速开始]({{< relref "/docs/start/quickstart/" >}})，准备 Python 3.10+。在控制台完成首次改密，再创建一个具有项目创建权限的个人 API Key；密钥明文仅在创建时展示一次。

在私有终端环境设置 `GL_API_KEY`。不要将值写进脚本、命令历史附件或版本库。客户端默认连接本机 gRPC 地址，其他地址通过 `GL_ENDPOINT` 配置。

## 1. 安装源码客户端

在快速开始检出的 GeoLedger 仓库根目录执行：

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ./sdk/python
```

该步骤从本地源码安装 `geoledger`，不依赖公开包注册表是否提供同版本。

## 2. 保存脚本

将以下内容保存为 `publish_station.py`：

```python
import os
from geoledger import Client

endpoint = os.environ.get("GL_ENDPOINT", "http://127.0.0.1:7882")
api_key = os.environ["GL_API_KEY"]

with Client(endpoint, api_key) as client:
    project = client.create_project("SDK 监测点演示")
    dataset = client.create_dataset(
        project.id, "stations", "point",
        coordinate_dimension=2, crs="EPSG:4326",
    )
    draft = client.create_workspace(project.id)
    draft.save(dataset.id, {
        "type": "Feature", "id": "station-001",
        "properties": {"name": "示例监测点", "sequence": 9007199254740993},
        "geometry": {"type": "Point", "coordinates": [120.15, 30.27]},
    })
    print("差异", draft.diff())
    receipt = draft.publish("新增示例监测点")
    snapshot = client.features(
        project.id, dataset.id, revision=receipt["revision"],
    )
    print("修订", receipt["revision"])
    print("要素", snapshot)
```

Feature 使用稳定字符串 ID。保存提交完整属性与几何；再次更新时先读取完整要素，保留未修改字段。

## 3. 运行并检查结果

```sh
python publish_station.py
```

核对差异包含 `station-001`，发布回执包含 `revision`，读取结果对应同一修订并保留 `sequence` 的整数值。在控制台的测试项目中查看同一提交与要素。

重复运行会创建另一个项目。遇到项目重名或配额拒绝时，调整测试项目名称或联系管理员，不以删除现有业务项目处理。

## 错误与后续接入

这个学习脚本在请求失败时退出。发布报错且结果不确定时，不要直接重跑整个脚本；保留原工作区与发布意图，按[确认与恢复发布]({{< relref "/docs/guides/publication-recovery/" >}})处理。

接入长期运行的应用时，补充业务错误处理、发布意图持久化和完整分页。语言差异见 [SDK 参考]({{< relref "/docs/reference/sdk/" >}})，游标处理见[分页与一致性]({{< relref "/docs/reference/pagination/" >}})。

## 实现依据

- [sdk/python/pyproject.toml](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/pyproject.toml)
- [sdk/python/geoledger/__init__.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/geoledger/__init__.py)
- [sdk/python/tests/smoke.py](https://github.com/mapseekai/geoledger/blob/5bf353c88cb017c8c00035fb86667dd2d7497b43/sdk/python/tests/smoke.py)
