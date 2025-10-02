# Touhou Memory Archive

## 项目简介

`Touhou Memory Archive` 是一个致力于东方 Project 相关视频信息归档与管理的项目。它由两个主要相关仓库组成，**均由我们维护**：

1.  **本仓库 (`touhou-memory-archive`)：** 核心功能是一个~~强大的~~ **Bilibili 视频信息爬虫**，用于抓取指定 UP 主的视频数据并存储。本仓库旨在成为东方 Project 视频数据的**核心生产者和管理者**。
2.  **数据展示仓库 (`touhou-memory-archive-data`)：** 这是一个独立的 Vue 3 项目，它会消费本仓库导出的 JSON 数据，并生成 GitHub Pages 静态网站，从而提供在线的视频信息展示和搜索功能。

这两个仓库独立运作但紧密协作，共同实现从数据获取、处理到最终展示的完整流程，为东方 Project 社区提供一个全面的视频内容归档解决方案。

## 项目愿景

东方 Project 拥有庞大而活跃的二次创作社区，尤其是在 Bilibili 等视频平台上有大量的优质内容。本项目旨在通过自动化方式，系统地收集和整理这些视频的核心信息，建立一个持久、可检索的资料库。这将有助于：

- 系统地收集和保存 Bilibili 上的东方 Project 视频数据。
- 为其他数据消费项目（如静态展示页面、API 服务）提供可靠的数据源。
- 方便社区成员通过不同渠道查找和回顾特定的东方 Project 视频内容。
- 长期保存重要的社区创作记录。

## 当前状态与模块说明

### `crawler/` (核心开发模块)

这个目录包含了项目的核心爬虫逻辑，目前是主要的开发重心。它负责：

- **爬取 Bilibili UP 主视频信息：** 通过 Bilibili API 抓取指定 UP 主的视频标题、封面、发布日期、~~播放量、点赞数、评论数、弹幕数~~等详细信息。
- **WBI 签名处理：** 内置 WBI 签名生成机制，以应对 Bilibili API 的鉴权要求。
- **数据存储：** 将爬取到的数据存储在一个 SQLite 数据库 (`bili-videos.db`) 中，以便后续查询和使用。
- **灵活配置：** 通过 `config.py` 文件允许用户自定义要爬取的 UP 主列表和其他爬虫参数。

**文件概览:**
- `config.py`: 爬虫配置文件，包含 UP 主列表、爬取间隔等设置。
- `database.py`: 数据库操作模块，负责与 SQLite 数据库交互。
- `fetcher.py`: 核心数据抓取逻辑，调用 Bilibili API。
- `main.py`: 爬虫程序的入口点。
- `init.sql`: 数据库初始化脚本，用于创建视频信息表。
- `delay_manager.py`, `video.py`, `wbi_singer.py`: 辅助模块，处理延迟、视频数据模型和 WBI 签名。

### `app/` (未来规划模块)

此目录结构用于未来在本仓库内开发的 Web 应用。它将独立于 `touhou-memory-archive-data` 仓库的静态页面，计划使用 **Python 作为后端** (例如 Flask 或 FastAPI) 和 **Vue 3 作为前端框架**。该模块的潜在功能包括：

- **独立的管理界面：** 提供更精细的视频数据管理功能。
- **自定义 API 服务：** 为本仓库或其他内部工具提供数据接口。
- **实验性功能展示：** 用于测试新的数据展示或交互方式。

### `scripts/export.py`

这是一个独立的辅助脚本，用于将 `bili-videos.db` 数据库中的视频数据导出为 JSON 格式。**这些导出的 JSON 数据旨在为我们的另一个项目 `touhou-memory-archive-data` 仓库提供数据源。** `touhou-memory-archive-data` 是一个独立的 Vue 3 项目，它会消费这些 JSON 数据来生成 GitHub Pages 静态网站，从而提供在线的视频信息展示和搜索功能。

## 技术栈

- **核心语言：** Python
- **数据存储：** SQLite
- **（本仓库未来 Web 应用）后端：** Python (例如 Flask/FastAPI)
- **（本仓库未来 Web 应用）前端：** Vue 3 (规划中)
- **（相关展示仓库 `touhou-memory-archive-data`）前端：** Vue 3
- **依赖：** 详见 `requirements.txt`

## 安装指南

以下说明将帮助你设置并运行爬虫模块。

1.  **克隆仓库：**
    ```bash
    git clone https://github.com/TouhouGleaners/touhou-memory-archive.git
    cd touhou-memory-archive
    ```
2.  **安装 Python 依赖：**
    确保你的系统安装了 Python 3。然后安装 `requirements.txt` 中列出的所有依赖。
    ```bash
    pip install -r requirements.txt
    ```

3.  **初始化数据库：**
    项目使用 SQLite 数据库 (`bili-videos.db`) 来存储爬取的数据。你需要运行 `crawler/init.sql` 脚本来创建必要的表结构。
    ```bash
    sqlite3 bili-videos.db < crawler/init.sql
    ```
    *注意：`bili-videos.db` 文件默认不在 Git 追踪中。*

4.  **配置爬虫：**
    进入 `crawler/` 目录，并复制示例配置文件 `config.py.example` 为 `config.py`。
    ```bash
    cp crawler/config.py.example crawler/config.py
    ```
    编辑 `crawler/config.py` 文件，根据你的需求进行配置。

## 使用方法

### 1. 运行视频信息爬虫

配置完成后，在项目根目录下运行 `main.py` 脚本来启动爬虫：
```bash
python crawler/main.py
```
爬虫将根据 `crawler/config.py` 中的设置开始工作，抓取数据并存储到 `bili-videos.db`。

### 2. 导出数据供外部项目使用

当你需要将数据库中的数据导出为 JSON 格式，以供如 `touhou-memory-archive-data` 等我们自己的其他项目使用时，可以运行 `export.py` 脚本：
```bash
python scripts/export.py
```
该脚本会将当前数据库中的数据导出为 JSON 格式。**你需要手动将这些 JSON 文件移动、提交并推送到 `touhou-memory-archive-data` 仓库。** 一旦数据被推送到 `touhou-memory-archive-data` 仓库，其 GitHub Pages 将会自动更新，提供最新的视频信息展示。

**在线浏览页面 (由 `touhou-memory-archive-data` 提供):**
你可以在以下地址访问由 `touhou-memory-archive-data` 生成的 GitHub Pages 静态站点：
[Touhou Memory Archive Data](https://touhougleaners.github.io/touhou-memory-archive-data/)

### 3. （本仓库未来）Web 应用

`app/` 模块的 Web 应用在开发完成后，将提供更详细的启动和使用说明。

## 贡献指南

我们非常欢迎对 `Touhou Memory Archive` 项目的贡献！如果你有改进建议、发现了 bug 或者想贡献代码，请通过以下方式：

- 在 GitHub 上提交 Issue 来报告 Bug 或提出功能请求。
- Fork 仓库，创建新的分支，提交你的修改，然后发起 Pull Request。

请确保你的代码遵循项目约定，并提供清晰的提交信息。

## 许可证

本项目采用 `MIT` 许可证。有关更多详细信息，请参阅 `LICENSE` 文件。

## 联系方式

如果您有任何问题或建议，可以通过 GitHub Issues 与我们联系。

---

**感谢你对 Touhou Memory Archive 的关注！**