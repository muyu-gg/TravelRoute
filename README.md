# 觅途行 · MiTuXing — AI 旅游路线规划系统

基于 **Django 4.2 + LangGraph + DeepSeek** 构建的智能旅游路线规划系统。用户输入目的地、预算、出行时间和偏好后，AI 自动完成意图识别、景点检索、路线构建、质量验证，生成包含每日行程、交通方案、费用预算的完整旅游规划。

## 功能概览

| 模块 | 说明 |
|------|------|
| AI 路线规划 | LangGraph Agent 驱动，自动调用意图识别→景点检索→路线构建→质量验证四步工具链 |
| 景点浏览 | 按城市/关键词/免费筛选，支持收藏与评论 |
| 旅游攻略 | 用户发布图文攻略，关联景点，支持搜索 |
| 高德地图 | 路线结果页展示多策略公交/地铁/驾车方案 |
| 后台管理 | SimpleUI 美化的 Django Admin，管理景点、攻略、规划记录 |

## 技术栈

- **后端**: Django 4.2 + MySQL + LangGraph + LangChain + OpenAI SDK
- **AI 模型**: DeepSeek Chat（兼容 OpenAI 接口）
- **地图服务**: 高德地图 Web 服务 API（地理编码 + 路径规划）
- **前端**: Django Templates + 高德地图 JS API
- **后台**: django-simpleui

## 项目结构

```
travel_route/
├── accounts/          # 用户认证（登录/注册/个人中心）
├── travel/            # 景点数据（浏览/收藏/评论）
├── guides/            # 旅游攻略（发布/搜索/详情）
├── planner/           # AI 路线规划核心
│   ├── agent/         # LangGraph Agent
│   │   ├── graph.py   # 状态图定义与运行
│   │   ├── tools.py   # Agent 工具（意图识别/景点检索/路线构建/质量验证）
│   │   └── utils/     # LLM 调用、提示词、JSON 工具、路线算法
│   ├── amap_service.py # 高德地图 API 封装
│   ├── services.py    # 规划业务逻辑（同步/流式）
│   └── views.py       # 规划视图 + 地图代理 API
├── travel_route/      # Django 项目配置
├── templates/         # HTML 模板
├── static/            # 静态资源（CSS/JS/图片）
├── sql/               # 数据库初始化 SQL
├── scripts/           # 辅助脚本（数据导入/爬虫/调试）
├── docs/              # 设计文档与提示词
├── start.py           # 一键启动脚本
├── stop.py            # 一键停止脚本
└── requirements.txt   # Python 依赖
```

## 快速开始

### 环境要求

- Python 3.9+
- MySQL 5.7+ / 8.0+
- Windows（一键启动脚本适配 Windows；手动启动不限平台）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/travel_route.git
cd travel_route
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下必要配置：

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | [platform.deepseek.com](https://platform.deepseek.com/) |
| `AMAP_SERVER_KEY` | 高德地图 Web 服务 Key | [lbs.amap.com](https://lbs.amap.com/) |
| `gaodeMap` | 高德地图 JS API Key（前端） | [lbs.amap.com](https://lbs.amap.com/) |
| `MYSQL_PASSWORD` | MySQL 密码 | 本地 MySQL 配置 |

### 3. 一键启动（Windows）

```bash
python start.py
```

脚本会自动完成：创建虚拟环境 → 安装依赖 → 检查 MySQL → 创建数据库 → 执行迁移 → 创建管理员 → 启动服务器。

默认管理员账号：`admin / admin123`

### 4. 手动启动（任意平台）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### 5. 访问系统

- 首页：http://127.0.0.1:8000/
- AI 路线规划：http://127.0.0.1:8000/planner/
- 后台管理：http://127.0.0.1:8000/admin/

## AI 路线规划工作流

```
用户输入（目的地/预算/时间/偏好）
        │
        ▼
  ┌─────────────┐
  │ 意图识别     │  parse_travel_intent
  │ (DeepSeek)  │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 景点检索     │  search_attractions
  │ (MySQL+排序) │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 路线构建     │  build_route_candidates
  │ (最近邻排序) │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 质量验证     │  validate_route_plan
  │ (折返检测)   │
  └──────┬──────┘
         │
         ▼
  Markdown 路线说明（行程表/交通方案/费用预算）
```

LangGraph 状态图支持流式输出（SSE），前端可实时展示规划过程每一步的进展。

## 数据导入

项目提供了 SQL 初始化脚本和 Python 数据导入工具：

```bash
# 使用 SQL 初始化表结构和种子数据
mysql -u root -p travel_route_base < sql/init_database.sql
mysql -u root -p travel_route_base < sql/attraction_data.sql
mysql -u root -p travel_route_base < sql/guide_seed_data.sql

# 或使用 Python 脚本导入
python scripts/db/import_data.py
python scripts/db/seed_data.py
```

## 停止服务

```bash
# Windows 一键停止
python stop.py

# 或在运行终端按 Ctrl+C
```

## 开发

```bash
# 运行开发服务器
python manage.py runserver

# 创建迁移
python manage.py makemigrations
python manage.py migrate
```

## 常见问题

**Q: 启动时提示 MySQL 连接失败？**

A: 请确保 MySQL 服务已启动，并检查 `.env` 中的 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD` 配置是否正确。

**Q: AI 路线规划提示 "未配置 DEEPSEEK_API_KEY"？**

A: 请在 `.env` 文件中填写有效的 DeepSeek API Key，或设置系统环境变量 `DEEPSEEK_API_KEY`。

**Q: 地图无法显示？**

A: 请在 `.env` 文件中配置高德地图 JS API Key（`gaodeMap`）和 Web 服务 Key（`AMAP_SERVER_KEY`）。

## License

[MIT](LICENSE)