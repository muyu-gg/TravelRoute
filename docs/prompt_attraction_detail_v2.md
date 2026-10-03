# 觅途行（MiTuXing）景点详情页 V2 —— AI 生成提示词

> 用途：把本文件整段复制给代码生成 AI（如 Claude / GPT / 通义灵码 / Cursor 等），即可生成升级版景点详情页的前端 + 后端 + 数据库 SQL。
> 使用前请先核对文中的【技术栈】与【接口约定】是否与你的实际项目一致。

---

## 0. 使用说明（给你自己看，不必发给 AI）

1. 技术栈和接口路径若与你的项目不同，先改【技术栈】【接口约定】两处再发。
2. 若只想让 AI 改前端、不动后端，把【接口约定】改为：「按现有接口对接，新增字段由后端补充返回」。
3. 建议让 AI 分两步执行：
   - 第一步：先输出 SQL 和「前端字段 → 数据库字段 → 接口字段」映射；
   - 你确认字段无误后，第二步再让它生成页面代码，返工率最低。
4. 数据库字段由你后续手动添加，AI 代码必须严格按本文约定的字段名对接。

---

## 1. 角色

你是一名资深全栈工程师，擅长旅游平台的前端页面开发与 MySQL 数据库设计。

---

## 2. 项目背景

我在开发一个名为「觅途行（MiTuXing）」的旅游平台。

- 当前景点详情页已完成 **V1 基础版本**；
- 现在需要按新的产品设计升级为 **V2**，并同步设计/确认数据库字段；
- 数据库字段我会负责最终添加，但你的代码必须严格按下方约定的字段名对接，保证后续接入即可用。

---

## 3. 技术栈（请按实际替换）

- 前端：Vue3 + Element Plus + Vite（如实际为其他技术栈请自行等价替换）
- 后端：Spring Boot（提供 REST API）
- 数据库：MySQL 5.7+

> 若以上与我的实际技术栈不符，请按我的技术栈实现，并在代码注释中标注可替换位置。

---

## 4. 当前页面现状（V1）

- 顶部导航栏：`首页 / 景点 / 攻略 / AI规划`，当前选中「景点」；
- 右上角显示登录用户名（如 `admin`）与「退出」按钮；
- 此框架保持不变；
- 页面主体：景点基础信息（名称、评分、评论数、收藏数、标签、状态）；
- 红色「已收藏」按钮、「携程详情」按钮；
- 评论区；
- 整体浅蓝色背景。

---

## 5. 目标效果（V2，由两张设计稿合并）

### 5.1 顶部宣传区

- 展示景点活动宣传大图 Banner（参考冬季主题宣传图样式）；
- 图上叠加活动名称与活动时间（如 `2024.11.23-2025.01.01`）；
- 若 `banner_url` 为空，显示默认渐变占位背景，不报错；
- Banner 旁展示：景点名称、标签（多个 tag，如「嗨玩乐园」「遛娃宝藏地」）、评分（如 `4.5`）、热度（如 `10.0`）、票价（如 `405.0`）。

### 5.2 收藏交互

- 展示收藏状态：已收藏 / 未收藏，按钮随状态切换样式（未收藏为主色，已收藏为红色）；
- 点击收藏按钮后调接口切换状态，并弹出 toast 提示「收藏成功」；
- 收藏数实时刷新。

### 5.3 信息面板（左右两栏卡片）

**左侧「景点信息」卡片**，逐项展示：

| 展示项 | 字段 |
| --- | --- |
| 唯一标识 | id |
| 评论数量 | comment_count |
| 是否推荐 | is_recommended（展示为 是/否） |
| 是否广告 | is_ad（展示为 是/否） |
| 距市中心 | distance_center（单位 km，如 24.0km） |
| 坐标 | longitude, latitude（如 116.68782, 39.86099） |

**右侧「票价信息」卡片**，逐项展示：

| 展示项 | 字段 |
| --- | --- |
| 实际票价 | actual_price |
| 市场票价 | market_price |
| 优惠价格 | discount_price（无则显示「暂无」） |
| 优惠描述 | discount_desc |
| 价格类型 | price_type |
| 价格说明 | price_desc（如「门票」） |

### 5.4 数据来源模块

- 说明文案：「当前展示的是本站 MySQL 保存的景点数据」；
- 橙色按钮「查看携程原始页面」，点击在新窗口打开 `ctrip_url` 对应链接。

### 5.5 用户评论模块

- 评论输入框 + 「发表评论」按钮；未登录用户点击时提示先登录，登录用户可发表；
- 评论列表展示：头像、用户名、内容、发表时间，按时间倒序；
- 无评论时显示占位文案：「暂无评论，快来发表第一条评论吧」；
- 发表成功后评论列表刷新，景点信息中的评论数量同步 +1。

---

## 6. 数据库字段约定

### 6.1 景点表 `spot`

以下字段必须存在且命名一致，前端展示与后端返回严格对齐：

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT | 唯一标识 |
| name | VARCHAR(100) | 景点名称 |
| rating | DECIMAL(3,1) | 评分 |
| heat | DECIMAL(6,2) | 热度 |
| comment_count | INT | 评论数量 |
| favorite_count | INT | 收藏数量 |
| tags | VARCHAR(255) | 标签，逗号分隔 |
| status | VARCHAR(50) | 状态（如「暂无」） |
| is_recommended | TINYINT(1) | 是否推荐，0/1 |
| is_ad | TINYINT(1) | 是否广告，0/1 |
| distance_center | DECIMAL(10,2) | 距市中心(km) |
| longitude | DECIMAL(10,6) | 经度 |
| latitude | DECIMAL(10,6) | 纬度 |
| actual_price | DECIMAL(10,2) | 实际票价 |
| market_price | DECIMAL(10,2) | 市场票价 |
| discount_price | DECIMAL(10,2) | 优惠价格，可空 |
| discount_desc | VARCHAR(100) | 优惠描述 |
| price_type | TINYINT | 价格类型 |
| price_desc | VARCHAR(100) | 价格说明 |
| banner_url | VARCHAR(255) | 宣传图 URL |
| activity_name | VARCHAR(100) | 活动名称 |
| activity_time | VARCHAR(100) | 活动时间 |
| data_source | VARCHAR(100) | 数据来源，默认「本站MySQL」 |
| ctrip_url | VARCHAR(255) | 携程详情链接 |
| created_at / updated_at | DATETIME | 创建/更新时间 |

### 6.2 评论表 `comment`

`id`、`spot_id`、`user_id`、`content`、`created_at`

### 6.3 收藏表 `favorite`

`id`、`user_id`、`spot_id`、`created_at`，并建 `(user_id, spot_id)` 唯一索引防止重复收藏。

### 6.4 建表 / ALTER SQL

同时给出以下 SQL（建表或 ALTER 均可）：

```sql
ALTER TABLE spot ADD COLUMN heat DECIMAL(6,2) DEFAULT 0 COMMENT '热度';
ALTER TABLE spot ADD COLUMN is_recommended TINYINT(1) DEFAULT 0 COMMENT '是否推荐';
ALTER TABLE spot ADD COLUMN is_ad TINYINT(1) DEFAULT 0 COMMENT '是否广告';
ALTER TABLE spot ADD COLUMN distance_center DECIMAL(10,2) DEFAULT 0 COMMENT '距市中心(km)';
ALTER TABLE spot ADD COLUMN longitude DECIMAL(10,6) DEFAULT 0 COMMENT '经度';
ALTER TABLE spot ADD COLUMN latitude DECIMAL(10,6) DEFAULT 0 COMMENT '纬度';
ALTER TABLE spot ADD COLUMN actual_price DECIMAL(10,2) DEFAULT 0 COMMENT '实际票价';
ALTER TABLE spot ADD COLUMN market_price DECIMAL(10,2) DEFAULT 0 COMMENT '市场票价';
ALTER TABLE spot ADD COLUMN discount_price DECIMAL(10,2) DEFAULT NULL COMMENT '优惠价格';
ALTER TABLE spot ADD COLUMN discount_desc VARCHAR(100) DEFAULT '' COMMENT '优惠描述';
ALTER TABLE spot ADD COLUMN price_type TINYINT DEFAULT 0 COMMENT '价格类型';
ALTER TABLE spot ADD COLUMN price_desc VARCHAR(100) DEFAULT '' COMMENT '价格说明';
ALTER TABLE spot ADD COLUMN banner_url VARCHAR(255) DEFAULT '' COMMENT '宣传图URL';
ALTER TABLE spot ADD COLUMN activity_name VARCHAR(100) DEFAULT '' COMMENT '活动名称';
ALTER TABLE spot ADD COLUMN activity_time VARCHAR(100) DEFAULT '' COMMENT '活动时间';
ALTER TABLE spot ADD COLUMN data_source VARCHAR(100) DEFAULT '本站MySQL' COMMENT '数据来源';
ALTER TABLE spot ADD COLUMN ctrip_url VARCHAR(255) DEFAULT '' COMMENT '携程详情链接';
```

---

## 7. 接口约定

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/spot/{id}` | 返回景点全部字段（含上表所有字段） |
| GET | `/api/spot/{id}/comments` | 分页返回评论列表 |
| POST | `/api/spot/{id}/comment` | 发表评论（需登录，body 含 content） |
| POST | `/api/spot/{id}/favorite` | 收藏/取消收藏（需登录，返回最新 favorite_count 与收藏状态） |

---

## 8. 实现要求

- 卡片式布局，浅蓝色背景，整体视觉与现有页面保持一致；
- 各模块抽成独立组件（Banner 区、信息面板、数据来源、评论列表）；
- 所有字段做空值兜底：`null` / 空串统一显示「暂无」或 `--`；
- 页面需响应式，常见分辨率下不错位；
- 不改动顶部导航栏和整体页面框架；
- 收藏按钮、发表评论等交互要有 loading 与成功/失败反馈。

---

## 9. 验收标准

1. 打开景点详情页，Banner、名称、标签、评分、热度、票价、收藏状态全部正常渲染；
2. 景点信息、票价信息两栏字段齐全且与数据库字段一一对应；
3. 数据来源模块文案与橙色按钮正确，点击能打开携程链接；
4. 发表评论后列表刷新、评论数 +1；无评论时显示占位文案；
5. 收藏点击后状态切换、toast 提示「收藏成功」、收藏数更新；
6. 任一时间题字段缺失时页面不报错，显示兜底文案。

---

## 10. 输出要求

1. 给出前端页面完整代码（组件 + 样式）；
2. 给出后端接口代码（Controller / Service / DAO 或等价分层）；
3. 给出完整 SQL（ALTER 或建表语句）；
4. 附一份「前端字段 → 数据库字段 → 接口字段」映射说明。
