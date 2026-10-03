# AI 路线规划助手 · 前端提示词文档（Prompt Playbook）

> 用途：把当前「纯默认表单」的页面（参考截图 4）优化成目标样式（参考截图 1–3）。
> 技术栈：**原生 Django（DTL 模板）+ Tailwind CSS（CDN 引入）**。
> 本文档既可当**优化说明**看，也可**整段复制给 AI 编码助手**直接生成代码。

---

## 〇、先给结论：当前问题 & 优化方向

| 维度 | 当前状态（截图 4） | 目标状态（截图 1–3） |
| --- | --- | --- |
| 布局 | 单列、表单裸奔、右侧大片空白 | 双栏网格 + 卡片分区 |
| 视觉 | 浏览器默认控件样式 | 白卡 + 3px 深描边 + 硬阴影（neo-brutalism） |
| 配色 | 无主题色 | 浅蓝底 `#eaf3fc` + 黄/橙/绿强调色 |
| 层次 | 无标题层级 | 小绿标(英文) + 大黑标题 的二级标题规范 |
| 结果区 | 缺失 | 路线结果卡 + 高德地图卡 + 景点卡片网格 |
| 反馈 | 无 | 规划过程时间线（编号步骤）、状态徽章 |

**优化一句话**：把所有内容装进「白卡 + 粗描边 + 硬阴影」的卡片系统，建立 `小绿标 / 大黑标题` 的标题规范，并用 Tailwind 工具类落地配色与网格。

---

## 一、设计令牌（Design Tokens）

把这段作为**提示词的一部分**，让 AI 统一套用：

```
配色：
- 页面背景 pagebg:  #eaf3fc（浅蓝）
- 卡片背景:          #ffffff
- 主描边/主文字 ink: #1f2a3a（近黑，深藏青）
- 小标签绿 green:    #16a34a
- 主按钮黄 accent:   #fcd34d
- 强调按钮橙 warn:   #f59e0b
- 成功绿 ok:         #22c55e

形状：
- 卡片圆角 rounded-2xl(16px)，输入框/按钮 rounded-xl(12px)，胶囊 rounded-full
- 卡片/按钮统一 3px 深色描边 border-[3px] border-ink
- 硬阴影 box-shadow: 6px 6px 0 0 #1f2a3a（小元素用 3px）
- 按钮按压反馈：active 时 translate 3px + 阴影归零

排版：
- 小标签：text-xs font-bold text-green uppercase tracking-widest
- 大标题：text-2xl/3xl font-black text-ink
- 正文：text-sm text-slate-600；字段值 font-bold text-ink
- 字体：Noto Sans SC / system-ui

Tailwind CDN 注意：
- Play CDN 不支持 @apply，全部写成 HTML 工具类
- 任意值里 # 用下划线代替逗号：shadow-[6px_6px_0_0_#1f2a3a]
```

---

## 二、目标页面结构（截图 1–3 拆解）

```
┌─ 顶部 Header 卡 ────────────────────────────────────────────┐
│ 绿标 LangGraph Agent                       [最近规划(黄)]    │
│ 大标题 AI路线规划助手                                        │
│ 说明：输入目的地、预算、时间和偏好，系统会实时展示 LangGraph │
│      执行过程并生成地图路线。                                │
└─────────────────────────────────────────────────────────────┘
┌─ 左：规划条件卡 ─────────────┐  ┌─ 右：LangGraph规划过程卡 ──┐
│ 绿标 Route Inputs            │  │ 绿标 Graph Process          │
│ 大标题 规划条件              │  │ 大标题 LangGraph规划过程    │
│ [目的地城市]  [旅行预算]     │  │ ①任务启动 说明…             │
│ [出行时间]                   │  │ ②输入接收 说明…             │
│ [旅行偏好 textarea]          │  │ ③LLM Agent 决策 …           │
│ [开始规划(橙)]               │  │ ④意图识别 … ⑤… (可滚动)     │
└──────────────────────────────┘  └─────────────────────────────┘
┌─ 左：路线结果卡 ─────────────┐  ┌─ 右：高德地图卡 ────────────┐
│ 绿标 AI Result               │  │ 绿标 Gaode Map              │
│ 大标题 路线结果              │  │ 大标题 高德地图路线          │
│ · 文字结果…                  │  │ [地图 + 编号标记1-12 + 路线]│
│ ✅路线检查结论：通过(100分)  │  │                             │
└──────────────────────────────┘  └─────────────────────────────┘
┌─ 景点行程卡网格（4 列 × 3 天）────────────────────────────────┐
│ [第1天·第1站 故宫博物院 …坐标] [第1天·第2站 恭王府] …          │
│ [第2天·第1站 北京环球度假区] …                                 │
│ [第3天·第1站 八达岭长城] …                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、可直接复制的「主提示词」（整页生成）

> 把下面整段丢给 AI 编码助手（Claude / GPT / Cursor 等），让它基于当前 Django 项目改造页面。

```
你是一名资深前端工程师，请改造一个原生 Django 项目里的页面。

【技术约束】
- 后端：原生 Django（DTL 模板），不用 DRF、不用前端框架。
- 样式：Tailwind CSS 通过 CDN 引入：
  <script src="https://cdn.tailwindcss.com"></script>
  Play CDN 不支持 @apply，所有样式必须写成 HTML 上的工具类。
- 页面放在 templates/ 下，用 {% extends "base.html" %} 继承。

【设计规范】（必须严格遵守）
- 页面背景 #eaf3fc；卡片白底；统一 3px 深色描边 #1f2a3a。
- 卡片样式：bg-white border-[3px] border-ink rounded-2xl shadow-[6px_6px_0_0_#1f2a3a] p-6。
- 按钮样式：border-[3px] border-ink rounded-xl font-bold px-5 py-3 shadow-[3px_3px_0_0_#1f2a3a]，
  按下时 active:translate-x-[3px] active:translate-y-[3px] active:shadow-none。
  黄色按钮 bg-[#fcd34d]，橙色按钮 bg-[#f59e0b]。
- 标题规范：每个卡内先一行绿色小标签(text-xs font-bold uppercase tracking-widest text-green-600)，
  再一行黑色大标题(text-2xl font-black text-ink)。
- 输入框：w-full bg-white border-[3px] border-ink rounded-xl px-4 py-3 focus:outline-none。

【页面结构】
1) 顶部 Header 卡：绿标 "LangGraph Agent"，大标题 "AI路线规划助手"，
   副说明文字，右侧黄色按钮 "最近规划"。
2) 两栏 grid(md:grid-cols-2 gap-6)：
   左卡 "规划条件"：字段 目的地城市、旅行预算、出行时间、旅行偏好(textarea)，
   底部橙色按钮 "开始规划"。
   右卡 "LangGraph规划过程"：一个可滚动的步骤时间线，每步为
   带圆角编号方块(绿描边) + 步骤标题 + 灰色说明的卡片。
3) 两栏：左卡 "路线结果"（富文本结果 + 底部 "路线检查结论：通过（评分100分）" 带绿色对勾）；
   右卡 "高德地图路线"（放一个地图容器 div，留给 JS 渲染）。
4) 景点行程网格 grid(md:grid-cols-2 lg:grid-cols-4 gap-5)：
   每个卡片 = 黄色胶囊徽章 "第X天·第X站" + 景点名(大黑) + 说明文字(sm灰)
   + 底部坐标(text-xs slate-400)。

【数据】
- 用 Django 模板变量渲染；表单用 {% csrf_token %}，POST 提交到当前视图。
- 遍历用 {% for %}；为空时给出空状态（虚线边框卡 + 提示语）。

请输出：base.html(可复用) 和 该页面的完整模板，以及必要的 view 上下文示例。
```

---

## 四、分模块提示词（可只改造局部）

### 4.1 卡片容器 & 标题规范

```
请定义一套 Tailwind 类组合用于「粗描边硬阴影卡片」：
容器：bg-white border-[3px] border-ink rounded-2xl shadow-[6px_6px_0_0_#1f2a3a] p-6
标题块：<p class="text-xs font-bold uppercase tracking-widest text-green-600">EN Label</p>
        <h2 class="text-2xl font-black text-ink mt-1">中文标题</h2>
请用它包裹页面里的每一个功能区，不要出现裸内容直接贴在页面背景上。
```

### 4.2 规划条件表单

```
请实现 "规划条件" 卡片：
- 4 个字段：目的地城市(input, 占位 "如：成都、北京、杭州")、旅行预算(input, "如：2000元、低预算、免费")、
  出行时间(input, "如：3天、周末2天")、旅行偏好(textarea rows=4, "如：自然风光、美食、历史文化")。
- 前两个字段用 grid md:grid-cols-2 并排，其余整行。
- 字段标签 font-bold text-sm mb-2；输入框统一白底 + 3px 描边 + rounded-xl。
- 底部橙色按钮 "开始规划"，带按压位移反馈。
```

### 4.3 LangGraph 规划过程时间线

```
请实现 "LangGraph规划过程" 卡片：
- 右侧内容区固定高度(max-h-[420px])并可滚动 overflow-y-auto。
- 每一步 = 卡片(bg-white border-2 border-ink rounded-xl p-3 flex gap-3)：
  左侧小方块(number)：w-9 h-9 grid place-items-center rounded-lg border-2 border-green-500
  text-green-600 font-black；右侧=步骤标题(font-bold) + 说明(text-sm text-slate-500)。
- 步骤示例：任务启动 / 输入接收 / LLM Agent 决策 / 意图识别 / …
```

### 4.4 路线结果 & 检查结论

```
请实现 "路线结果" 卡片：上半部分渲染富文本结果(支持 ul/li、加粗、小标题)，
下半部分为 "路线检查结论" 区块：标题带 📋 图标，
下面一行 "✅ 检查结果：通过（评分 100 分）" 用绿色文字，
再接若干条 bullet 结论。
右卡 "高德地图路线" 放一个 <div id="map" class="w-full h-[360px] rounded-xl border-[3px] border-ink bg-slate-100"></div>。
```

### 4.5 景点行程卡片网格

```
请实现景点行程网格：grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5。
单个卡片 = bg-white border-[3px] border-ink rounded-2xl shadow-[6px_6px_0_0_#1f2a3a] p-5：
- 顶部黄色胶囊徽章：inline-block px-3 py-1 rounded-full bg-[#fcd34d] border-2 border-ink
  text-xs font-bold → "第{n}天 · 第{m}站"
- 景点名 text-lg font-black mt-3
- 说明 text-sm text-slate-500 mt-2（含标签、评分、门票参考、适配偏好）
- 底部坐标 text-xs text-slate-400 mt-3 → "116.403414, 39.924091"
用 {% for %} 遍历后端传入的行程列表。
```

### 4.6 最近规划列表（截图 4 保留功能）

```
请把当前的 "最近规划" 列表改造成符合整体风格的样式：
标题 "最近规划" font-black；列表每行 flex justify-between：
左侧城市名(font-bold)、中间状态徽章 "规划成功"(绿字/绿描边小胶囊)、右侧时间(text-sm text-slate-400)。
外层用白卡 + 3px 描边 + 硬阴影包裹，行间用 divide-y divide-dashed。
```

---

## 五、优化后的自检清单（对照截图 1–3）

- [ ] 页面背景为浅蓝 `#eaf3fc`
- [ ] 每个功能区都是「白卡 + 3px 深描边 + 硬阴影」
- [ ] 每个卡有「绿色英文小标 + 黑色中文大标题」
- [ ] 顶部含 `最近规划` 黄色按钮
- [ ] 规划条件 4 字段 + 橙色 `开始规划` 按钮
- [ ] LangGraph 过程为编号步骤时间线，可滚动
- [ ] 有「路线结果」卡与「高德地图路线」卡（双栏）
- [ ] 有「路线检查结论：通过（评分100分）」绿色通过标识
- [ ] 景点卡片为 4 列网格，含 `第X天·第X站` 黄色胶囊 + 坐标
- [ ] 所有按钮有按压位移反馈
- [ ] 窄屏能响应式折叠（grid-cols-1）

---

## 六、常见坑（给 AI 的额外约束）

```
- Tailwind Play CDN 不支持 @apply，禁止用 @layer/@apply 抽公共类。
- 任意值里空格用下划线、# 直接写：shadow-[6px_6px_0_0_#1f2a3a]。
- border-[3px] 必须配合 border-ink 上色，否则只有宽度没有颜色。
- {% csrf_token %} 不能漏，否则 POST 403。
- 地图容器先留 div，避免直接写死第三方地图 key。
- 中文不要用 \u 转义，直接写中文。
```

> 说明：本文档为通用前端开发参考，不构成任何投资建议。金融市场存在风险，相关决策请独立判断并自行承担风险。
