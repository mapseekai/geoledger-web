# GeoLedger Web

GeoLedger 的独立介绍与文档网站，基于 **Hugo Extended 0.168.0 + OINK v1.4.0**。首页解释产品与协作流程，Docs 按教程、操作指南、技术参考和概念解释组织，运维指南单独提供入口。Blog 区分正式发布与主分支工程记录。

网站沿用 GeoLedger 控制台的橙色强调、深色导航和中性灰白界面。内容基线保存在 `data/project.json`：源码 `0.3.0-alpha.7`、存储格式 `19`、提交 `5bf353c88cb017c8c00035fb86667dd2d7497b43`。

[在线文档](https://mapseekai.github.io/geoledger-web/) | [网站源码](https://github.com/mapseekai/geoledger-web) | [GeoLedger 项目](https://github.com/mapseekai/geoledger)

## 本地运行

需要 Go 1.27.3、Hugo **Extended** 0.168.0，以及用于检查的 Python 3.10+。网站本身不需要 Node.js，不依赖运行中的 GeoLedger 服务，也不读取业务数据库。

当前工作机的项目专用 Hugo 位于 `.tools/hugo`，不覆盖全局安装。该目录不进入 Git；新环境请从 Hugo 官方 release 安装匹配版本，或将二进制放到 `.tools/hugo`。

```sh
git clone https://github.com/mapseekai/geoledger-web.git
cd geoledger-web
go mod download
./scripts/dev.sh
```

在这台机器打开 `http://localhost:1313/`。开发服务器默认只监听回环地址，不自动向局域网或公网开放。

开发服务器在内存中渲染，与正式构建的 `public/` 目录隔离。运行发布构建或子路径检查时，不会覆盖本地预览的资源地址。

```sh
# 需要不同端口时
PORT=1314 ./scripts/dev.sh
```

## 生成静态网站

```sh
./scripts/build.sh
```

结果位于 `public/`。发布前必须显式设置实际站点地址，确保 canonical、RSS、搜索索引、图片和站内链接正确；默认值只用于本机预览。

```sh
BASE_URL=https://mapseekai.github.io/geoledger-web/ ./scripts/build.sh
```

正式站点由 GitHub Pages 托管。推送到 `main` 或手动运行网站工作流后，先执行构建和内容检查，再上传 `public/` 并部署到 `github-pages` 环境；Pull Request 只验证，不发布。首次部署需要将仓库的 Pages 构建来源设为 GitHub Actions。

网站的编辑与历史链接指向本仓库，产品源码与问题入口指向 GeoLedger。部署产物不包含 `.cache/`、`.tools/`、`artifacts/` 或数据库。

## 检查

```sh
./scripts/check.sh
```

检查包括生产构建、内容与验证器契约测试，以及生成 HTML 的站内资源、锚点、语言、标题和图片元数据。文档命令的 shell 语法、JSON 与 Python 代码块语法也会检查；这不代表已启动业务服务执行示例。外部网站可用性不在离线检查范围内。

独立验证子路径：

```sh
BASE_URL=https://example.invalid/geoledger/ ./scripts/build.sh --destination .cache/subpath-public
python3 scripts/check_site.py .cache/subpath-public --base-url https://example.invalid/geoledger/
```

浏览器交互验证通过当前机器的 `ego-browser` 执行，涵盖导航、搜索、深浅色、移动布局与 Mermaid 渲染；结果和截图写入 gitignored `artifacts/`。

```sh
./scripts/browser-check.sh
```
自动测试结果不能替代生产环境性能验收。

OINK v1.4.0 使用 Hugo 内置 LibSass，构建目前会产生一条上游弃用警告。本站已经修正自身的 `languageCode` / `.Site.Data` 弃用用法，不屏蔽上游警告或篡改下载的主题。

## 内容与设计结构

```text
content/
  _index.md                  首页的机器可读摘要
  docs/
    start/                   核心对象、启动、第一次发布、Python SDK 教程
    guides/                  控制台、工作区、PostGIS、字段、历史、发布恢复
    reference/               版本兼容性、SDK、HTTP、CLI、分页、配置
    architecture/            总览、版本、合并、存储、事务解释
    operations/              部署、身份安全、备份、故障诊断
  blog/                      Release 与 Main 记录
layouts/
  index.html                 定制首页，保留 OINK 全站外壳
  _partials/                 CSS 注入与页脚
  _shortcodes/               架构图与带来源说明的截图
  docs/                      文档类型与适用源码提示，复用主题内容钩子
assets/css/geoledger.css      品牌样式与响应式布局
static/images/               SVG 架构图和真实控制台测试截图
data/project.json            源码与工具链基线
data/screenshots.json        截图版本、日期、尺寸、摘要与来源
scripts/                     构建与离线检查
integration/                 检查器和内容契约测试
```

采用主题自带的目录、折叠侧栏、本地搜索、代码复制、Markdown 输出、`llms.txt`、RSS、Mermaid 和外观切换。品牌定制位于站点层，不复制或修改 OINK 源码。

## 更新内容

先固定 GeoLedger 提交，核对 README、协议、Manifest 和实现，再修改相关文档。接口示例不能从旧文章推断。正式 Release 日期与主分支提交日期分别记录，不能把 `main` 上的修复自动归入旧发布产物。

更新版本时同步 `data/project.json`、首页版本提示、相关文档与 Blog，并运行完整检查。新增页面需要标题、描述、导航权重、合适的阅读路径和实际实现依据。文档类型通过章节 cascade 继承 `doc_type`，混合入口中的概念页可单独覆盖；所有原有文档网址保留。

源码提交与发布标签分别记录在 `content/docs/reference/compatibility.md`。快速开始必须检出 `data/project.json` 中的固定提交；同版本字符串不证明主分支与发布产物行为一致。未执行产品流程的教程和操作页显示“待隔离实例验证”，正式环境使用前应完成对应验证。

## 截图的来源边界

网站包含 4 张项目既有浏览器测试截图，原始像素未修改。地图为 2026-10-22 alpha.6；工作区与历史为 2026-10-15 alpha.3；字段发布为 2026-10-26 alpha.7。图下注明日期和可见版本，不将旧截图冒充当前源码的新截图。

本次另建了隔离 alpha.7 演示实例，但首次修改初始密码的操作受当前工具安全检查限制，未绕过该流程，也未因此改写用户已有服务或数据库。后续刷新截图应在完成正常登录流程的独立测试实例中进行；提交前检查凭据、个人信息和业务数据，更新 `data/screenshots.json` 的尺寸与 SHA-256。

## 许可

本站自有代码与内容采用 MIT。GeoLedger 的 Logo 和真实界面图沿用上游项目许可；OINK 通过 Hugo Modules 引用，采用 Apache-2.0。完整说明见 `THIRD_PARTY_NOTICES.md` 和 `licenses/`。
