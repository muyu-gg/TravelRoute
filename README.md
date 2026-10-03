<div align="center">

# 觅途行 · MiTuXing

### AI 旅游路线规划系统

基于 Django 4.2 + LangGraph + DeepSeek 构建的智能旅游路线规划系统

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://djangoproject.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4%2B-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[功能介绍](#-功能介绍) · [快速开始](#-快速开始) · [技术架构](#-技术架构) · [项目结构](#-项目结构) · [API 说明](#-api-说明)

</div>

---

## ✨ 功能介绍

### 🗺️ AI 路线规划（核心功能）

用户输入目的地、预算、出行时间和偏好后，LangGraph Agent 自动驱动四步工具链：

```
用户输入 ──→ 意图识别 ──→ 景点检索 ──→ 路线构建 ──→ 质量验证 ──→ 完整规划
```

| 步骤 | 工具 | 说明 |
|:----:|------|------|
| 1 | `parse_travel_intent` | DeepSeek 识别目的地、天数、预算类型、节奏偏好 |
| 2 | `search_attractions` | MySQL 全文检索 + 评分/热度/偏好/预算多维排序 |
| 3 | `build_route_candidates` | 最近邻贪心排序，按天数分配每日 4 站，生成经纬度站点 |
| 4 | `validate_route_plan` | 折返检测 + 评分，不通过则 Agent 自主重试（最多 1 次） |

输出包含：**行程概览表 → 每日详细行程 → 交通方案对比 → 费用预算表 → 实用贴士**，全部 Markdown 格式化。

支持 **SSE 流式输出**，前端实时展示每一步进展（意图识别 → 景点检索 → 路线生成 → 质量检查 → 最终方案）。

### 🏛️ 景点浏览

- 按城市、关键词、免费/付费筛选
- 景点详情页展示评分、热度、票价、标签、活动信息
- 登录用户可**收藏**和**评论**

### 📖 旅游攻略

- 用户发布图文攻略，关联景点
- 按城市和关键词搜索
- 浏览量统计

### 🧭 高德地图集成

- 路线结果页展示多策略公交/地铁/驾车方案
- 支持 8 种公交策略：推荐 / 最经济 / 最少换乘 / 最少步行 / 最舒适 / 不乘地铁 / 地铁优先 / 时间最短
- 后端代理 API 保护服务端 Key 不暴露到前端

### ⚙️ 后台管理

- SimpleUI 美化的 Django Admin
- 自定义菜单：景点数据 / 攻略管理 / AI路线规划 / 账号权限
- 管理景点、攻略、规划记录、用户

---

## 🚀 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.9+ | 推荐 3.10 / 3.11 |
| MySQL | 5.7+ / 8.0 | 数据库 |
| DeepSeek API Key | — | [获取地址](https://platform.deepseek.com/) |
| 高德地图 Key | — | [获取地址](https://lbs.amap.com/) |

### 1. 克隆项目

```bash
git clone https://gitee.com/love-dry-rice/travel-assistant.git
cd travel-assistant
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填写以下必要配置：

| 变量 | 说明 | 必填 |
|------|------|:----:|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | ✅ |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址（默认 `https://api.deepseek.com`） | ❌ |
| `DEEPSEEK_MODEL` | 模型名称（默认 `deepseek-chat`） | ❌ |
| `AMAP_SERVER_KEY` | 高德地图 Web 服务 Key（后端路径规划） | ✅ |
| `gaodeMap` | 高德地图 JS API Key（前端地图展示） | ✅ |
| `MYSQL_PASSWORD` | MySQL 密码 | ✅ |
| `MYSQL_DATABASE` | 数据库名（默认 `travel_route_base`） | ❌ |
| `DJANGO_SECRET_KEY` | Django 密钥（生产环境必填） | ⚠️ |

### 3. 一键启动（Windows）

```bash
python start.py
```

脚本自动完成：创建虚拟环境 → 安装依赖 → 检查 MySQL → 创建数据库 → 执行迁移 → 创建管理员 → 启动服务器。

默认管理员：`admin / admin123`

### 4. 手动启动（任意平台）

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### 5. 访问系统

| 页面 | 地址 |
|------|------|
| 首页 | http://127.0.0.1:8000/ |
| AI 路线规划 | http://127.0.0.1:8000/planner/ |
| 景点浏览 | http://127.0.0.1:8000/travel/ |
| 旅游攻略 | http://127.0.0.1:8000/guides/ |
| 后台管理 | http://127.0.0.1:8000/admin/ |

---

## 🏗️ 技术架构

### 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | Django 4.2 |
| 数据库 | MySQL（mysqlclient 驱动） |
| AI Agent | LangGraph + LangChain + OpenAI SDK |
| LLM | DeepSeek Chat（兼容 OpenAI 接口） |
| 地图服务 | 高德地图 Web 服务 API v3/v5 |
| 前端 | Django Templates + 高德地图 JS API v2.0 |
| 后台 | django-simpleui 2024.8 |
| 环境管理 | python-dotenv |

### LangGraph Agent 状态图

```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         │
                         ▼
                   ┌───────────┐
                   │   agent   │  LLM + Tool Binding
                   │  (决策节点) │
                   └───┬───┬───┘
                       │   │
              有工具调用 │   │ 无工具调用（生成最终回答）
                       │   │──────────────────→ END
                       ▼
                 ┌───────────┐
                 │   tools   │  ToolNode 执行工具
                 └─────┬─────┘
                       │
                       ▼
                 ┌───────────┐
                 │   sync    │  同步工具输出到结构化状态
                 └─────┬─────┘
                       │
                       └──────→ agent（循环决策）
```

**PlannerState** 核心字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `messages` | `list[AnyMessage]` | LangChain 消息历史 |
| `city` / `budget` / `travel_time` / `preferences` | `str` | 用户输入 |
| `intent` | `dict` | 意图识别结果 |
| `candidates` | `list[dict]` | 候选景点列表 |
| `route_stops` | `list[dict]` | 排序后的路线站点 |
| `validation_result` | `dict` | 质量验证结果 |
| `final_plan` | `str` | 最终 Markdown 路线说明 |
| `process_steps` | `list[dict]` | 前端展示的步骤进度 |

### 数据模型

```
User (accounts)          Attraction (travel)          TravelGuide (guides)
├── username             ├── poi_id (唯一标识)         ├── title
├── avatar               ├── name / city_name          ├── city / summary / content
├── ...                  ├── score / heat_score        ├── view_count
                         ├── market_price / is_free   ├── images (M2M via TravelGuideImage)
AttractionFavorite       ├── longitude / latitude     └── guide_attractions (M2M via TravelGuideAttraction)
├── user → User          └── tags / image / banner_url
├── attraction → Attraction
                         RoutePlan (planner)          RoutePlanStop (planner)
AttractionComment        ├── city / budget / ...      ├── plan → RoutePlan
├── user → User          ├── intent_data (JSON)       ├── attraction → Attraction
├── attraction → Attraction ├── process_steps (JSON)   ├── day_index / sequence
├── content              ├── final_plan (Text)         ├── name / longitude / latitude
└── created_at           └── status (running/success/failed)  └── intro
```

---

## 📁 项目结构

```
travel_route/
├── accounts/                    # 用户认证
│   ├── models.py                #   User 模型（AbstractUser + 头像）
│   ├── views.py                 #   注册/登录/个人中心/收藏/评论
│   └── urls.py
├── travel/                      # 景点数据
│   ├── models.py                #   Attraction / AttractionFavorite / AttractionComment
│   ├── views.py                 #   景点列表/详情/收藏/评论
│   └── urls.py
├── guides/                      # 旅游攻略
│   ├── models.py                #   TravelGuide / TravelGuideImage / TravelGuideAttraction
│   ├── views.py                 #   攻略列表/详情/发布/搜索
│   └── urls.py
├── planner/                     # AI 路线规划核心
│   ├── agent/
│   │   ├── graph.py             #   LangGraph 状态图：build_route_graph / run / stream
│   │   ├── tools.py             #   4 个 Agent 工具定义
│   │   └── utils/
│   │       ├── llm.py           #     DeepSeek 模型初始化与调用
│   │       ├── prompt_utils.py  #     意图识别 + Agent 系统提示词
│   │       ├── attraction_repository.py  #     景点数据库检索
│   │       ├── route_utils.py   #     最近邻排序 + 质量验证
│   │       └── json_utils.py    #     JSON 安全解析/序列化
│   ├── amap_service.py          #   高德地图 API（地理编码/逆地理编码/公交/驾车/步行）
│   ├── services.py              #   规划业务逻辑（同步/流式 + 结果持久化）
│   ├── models.py                #   RoutePlan / RoutePlanStop
│   ├── views.py                 #   规划页面 + SSE 流式 + 地图代理 API
│   └── urls.py
├── travel_route/                # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/                   # HTML 模板
│   ├── base.html
│   ├── accounts/
│   ├── travel/
│   ├── guides/
│   └── planner/
├── static/                      # 静态资源
│   ├── css/
│   ├── js/
│   ├── img/
│   └── fonts/
├── sql/                         # 数据库初始化 SQL
├── scripts/                     # 辅助脚本（数据导入/爬虫/调试）
├── docs/                        # 设计文档与提示词参考
├── start.py                     # 一键启动脚本（Windows）
├── stop.py                      # 一键停止脚本
├── manage.py                    # Django 管理入口
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
└── .gitignore
```

---

## 📡 API 说明

### 路线规划

| 接口 | 方法 | 说明 |
|------|------|------|
| `/planner/` | GET | 规划表单页 |
| `/planner/plan/` | POST | 提交规划（同步模式） |
| `/planner/plan/stream/` | POST | 提交规划（SSE 流式模式） |
| `/planner/result/<id>/` | GET | 查看规划结果 |
| `/planner/history/` | GET | 规划历史列表 |

### 高德地图代理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/planner/api/amap/geocode/` | GET | 地理编码代理 |
| `/planner/api/amap/transit/` | GET | 公交路径规划代理 |
| `/planner/api/amap/driving/` | GET | 驾车路径规划代理 |
| `/planner/api/amap/walking/` | GET | 步行路径规划代理 |

> 代理接口在前端请求高德 API 时，由后端注入 `AMAP_SERVER_KEY`，避免密钥暴露到浏览器。

---

## 🗄️ 数据导入

项目提供 SQL 初始化脚本和 Python 导入工具：

```bash
# SQL 方式
mysql -u root -p travel_route_base < sql/init_database.sql
mysql -u root -p travel_route_base < sql/attraction_data.sql
mysql -u root -p travel_route_base < sql/guide_seed_data.sql

# Python 脚本方式
python scripts/db/import_data.py
python scripts/db/seed_data.py
```

---

## 🛑 停止服务

```bash
python stop.py        # Windows 一键停止
# 或在运行终端按 Ctrl+C
```

---

## 🔧 开发

```bash
python manage.py runserver              # 启动开发服务器
python manage.py makemigrations         # 生成迁移文件
python manage.py migrate                # 执行迁移
python manage.py createsuperuser        # 创建管理员
python manage.py shell                  # Django Shell
```

---

## ❓ 常见问题

<details>
<summary><b>启动时提示 MySQL 连接失败？</b></summary>

确保 MySQL 服务已启动，检查 `.env` 中 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD` 是否正确。默认连接 `127.0.0.1:3306`。

</details>

<details>
<summary><b>AI 路线规划提示 "未配置 DEEPSEEK_API_KEY"？</b></summary>

在 `.env` 文件中填写有效的 DeepSeek API Key，或设置系统环境变量 `DEEPSEEK_API_KEY`。可在 [platform.deepseek.com](https://platform.deepseek.com/) 免费申请。

</details>

<details>
<summary><b>地图无法显示或路径规划失败？</b></summary>

需要配置两个高德地图 Key：
- `gaodeMap`：JS API Key，用于前端地图展示
- `AMAP_SERVER_KEY`：Web 服务 Key，用于后端路径规划

两者可在 [lbs.amap.com](https://lbs.amap.com/) 免费申请。

</details>

<details>
<summary><b>如何替换为其他 LLM（如 OpenAI GPT）？</b></summary>

修改 `.env` 中的配置：
```
DEEPSEEK_API_KEY=sk-your-openai-key
DEEPSEEK_BASE_URL=https://api.openai.com/v1
DEEPSEEK_MODEL=gpt-4o
```
由于使用 OpenAI 兼容接口，任何兼容 OpenAI API 的模型均可直接替换。

</details>

---

## 🤝 参与贡献

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交改动：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

---

## 📄 开源许可

本项目基于 [MIT License](LICENSE) 开源。

---

<div align="center">

**觅途行 · 让 AI 为你规划每一段旅程**

</div>