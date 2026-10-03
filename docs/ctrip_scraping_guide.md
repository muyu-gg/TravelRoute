# 携程景点数据爬取指南

## 一、概述

本项目使用 **browser-harness** 插件通过 CDP（Chrome DevTools Protocol）控制真实 Chrome 浏览器，从携程景点列表页爬取真实景点数据并入库到 Django 数据库。

核心脚本：`scrape_ctrip_real.py`

---

## 二、环境要求

### 2.1 Chrome 浏览器

- 已安装 Chrome 浏览器（任意版本均可）
- 启动时需开启 CDP 调试端口

### 2.2 browser-harness 插件

- 安装位置：`C:\Users\29346\AppData\Roaming\Python\Python314\Scripts\browser-harness.exe`
- 版本：0.1.13
- 依赖 Python 3.14+（系统 Python，非项目 venv）
- 安装方式：`pip install browser-harness`（需在系统 Python 3.14 环境下）

### 2.3 项目 Python 环境

- 项目 venv：Python 3.11
- Django 已配置，数据库可正常连接
- 模型：`travel.models.Attraction`

### 2.4 关键环境变量

- `PYTHONPATH` 需包含 `C:\Users\29346\AppData\Roaming\Python\Python314\site-packages`（browser-harness 模块路径）
- `DJANGO_SETTINGS_MODULE=travel_route.settings`

---

## 三、操作步骤

### 步骤 1：启动 Chrome 调试模式

**必须先彻底关闭所有 Chrome 进程**，然后启动带 CDP 端口的 Chrome：

```powershell
# 1. 关闭所有 Chrome 进程
Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue

# 2. 启动 Chrome 调试模式
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList @"
--remote-debugging-port=9222
--no-first-run
--user-data-dir=$env:TEMP\chrome-cdp-profile
"@
```

> **注意**：如果 Chrome 未完全关闭，CDP 端口不会生效，browser-harness 将连接失败。

### 步骤 2：运行爬取脚本

```powershell
# 进入项目目录
cd "D:\BaiduNetdiskDownload\S028 基于Python+LangGraph的旅游规划系统与实现\赠送资料\travel_route\travel_route"

# 爬取所有城市（每城市2页，约20个景点/页）
.\venv\Scripts\python.exe scrape_ctrip_real.py --pages 2

# 只爬取指定城市
.\venv\Scripts\python.exe scrape_ctrip_real.py --city 北京 --pages 3

# 爬取更多页
.\venv\Scripts\python.exe scrape_ctrip_real.py --pages 5
```

### 步骤 3：验证数据

```powershell
.\venv\Scripts\python.exe -c "
import os,sys,django
os.environ['DJANGO_SETTINGS_MODULE']='travel_route.settings'
sys.path.insert(0,'.')
django.setup()
from travel.models import Attraction
from django.db.models import Count
print(f'总景点数: {Attraction.objects.count()}')
for c in Attraction.objects.values('city_name').annotate(cnt=Count('id')).order_by('-cnt'):
    print(f'  {c[\"city_name\"]}: {c[\"cnt\"]} 个')
"
```

---

## 四、脚本参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--city` | 只爬取指定城市（如 `北京`） | 爬取所有配置城市 |
| `--pages` | 每个城市爬取的页数 | 5 |

---

## 五、支持的城市列表

脚本内 `CTRIP_CITIES` 字典定义了城市与携程 URL slug 的映射：

| 城市 | 携程 Slug |
|------|-----------|
| 北京 | beijing1 |
| 上海 | shanghai2 |
| 广州 | guangzhou152 |
| 深圳 | shenzhen144 |
| 成都 | chengdu104 |
| 杭州 | hangzhou14 |
| 西安 | xian7 |
| 苏州 | suzhou9 |
| 南京 | nanjing12 |
| 重庆 | chongqing158 |
| 武汉 | wuhan17 |
| 长沙 | changsha148 |
| 郑州 | zhengzhou4 |
| 昆明 | kunming1 |
| 大理 | dali111 |
| 丽江 | lijiang31 |
| 厦门 | xiamen53 |
| 青岛 | qingdao3 |
| 大连 | dalian4 |
| 哈尔滨 | haerbin151 |
| 天津 | tianjin5 |
| 三亚 | sanya61 |
| 桂林 | guilin3 |
| 黄山 | huangshan18 |
| 洛阳 | luoyang98 |

如需添加新城市，在 `CTRIP_CITIES` 字典中添加 `城市名: slug` 映射即可。

---

## 六、数据提取逻辑

### 6.1 携程页面结构

携程景点列表页 URL 格式：`https://you.ctrip.com/sight/{slug}/s0-p{page}.html`

每个景点卡片 DOM 结构：
- 卡片容器：`[class*="sightItemCard"]`
- 景点名称：`[class*="titleModule_name"] a`
- 景点链接：`a` 元素的 `href` 属性，从中提取 `poiId`
- 评分、评论数、价格、等级等通过正则从卡片文本中提取

### 6.2 提取的字段

| 字段 | 提取方式 | 入库字段 |
|------|----------|----------|
| 景点名称 | DOM 选择器 | `name` |
| poiId | 链接正则 `/sight/{slug}/(\d+)` | `poi_id` |
| 评分 | 正则 `(\d+\.\d+)/5` | `score` |
| 评论数 | 正则 `([\d.]+万?条点评)` | `comment_count` |
| 价格 | 正则 `¥(\d+)` | `market_price` / `actual_price` |
| 是否免费 | 文本包含"免费" | `is_free` |
| 距市中心 | 正则 `距市中心([\d.km]+)` | `distance` / `distance_center` |
| 等级 | 正则 `(5A|4A|3A)` | `tags` |
| 封面图 | `img[class*="coverModule"]` 的 src | `image` |
| 详情链接 | 拼接 `https://you.ctrip.com/sight/{slug}/s{poiId}.html` | `detail_url` |

### 6.3 入库策略

使用 Django ORM 的 `update_or_create`，以 `poi_id` 为主键：
- 如果 `poi_id` 已存在 → 更新所有字段
- 如果 `poi_id` 不存在 → 新增记录

---

## 七、browser-harness 调用方式

脚本通过 `subprocess` 调用 browser-harness，关键代码：

```python
env = os.environ.copy()
env['PYTHONPATH'] = r'C:\Users\29346\AppData\Roaming\Python\Python314\site-packages'
result = subprocess.run(
    f'python -m browser_harness.run < "{script_path}"',
    capture_output=True,
    timeout=timeout,
    shell=True,
    env=env,
)
```

**注意事项**：
1. 必须设置 `PYTHONPATH` 指向 browser-harness 的 site-packages 目录
2. 使用 `python -m browser_harness.run` 而非 `browser-harness.exe`（避免 exe 的模块查找问题）
3. 脚本内容写入临时文件，通过 stdin 管道传入
4. 超时默认 60 秒，携程页面加载较慢时可适当增加

---

## 八、browser-harness 脚本语法

每个页面的爬取脚本包含以下 browser-harness 命令：

```
new_tab("https://you.ctrip.com/sight/beijing1/s0-p1.html")
wait_for_load(timeout=20)
import time
time.sleep(8)
data = js("""(function() { ... })()""")
print("RESULT:", data)
```

- `new_tab(url)` — 打开新标签页
- `wait_for_load(timeout=20)` — 等待页面加载
- `time.sleep(8)` — 额外等待 8 秒，确保 JS 渲染完成
- `js(...)` — 执行 JavaScript 提取数据
- `print("RESULT:", data)` — 输出结果，Python 端通过 `RESULT:` 前缀解析

---

## 九、注意事项与常见问题

### 9.1 Chrome CDP 连接失败

**症状**：browser-harness 输出 `DevToolsActivePort not found` 或连接超时

**解决**：
1. 彻底关闭所有 Chrome 进程：`Stop-Process -Name chrome -Force`
2. 重新启动带 CDP 端口的 Chrome（见步骤 1）
3. 确认端口 9222 已监听：`netstat -an | findstr 9222`

### 9.2 携程反爬机制

携程对爬虫有一定限制，但 browser-harness 使用真实浏览器，一般不会被拦截。如果遇到：
- **验证码**：手动在 Chrome 中完成验证，然后重新运行脚本
- **IP 限制**：降低爬取频率，增大 `time.sleep` 的等待时间
- **页面空白**：可能是 JS 渲染未完成，增大 `time.sleep` 时间

### 9.3 页面无数据

部分城市页面可能返回空数据（如大理、桂林、青岛），原因：
- 携程 slug 不正确（需在浏览器中手动验证）
- 页面结构变化（需更新 DOM 选择器）
- 网络问题

**排查方法**：在 Chrome 中手动打开对应 URL，确认页面是否正常显示景点列表。

### 9.4 数据去重

脚本在每城市内按 `poiId` 去重，跨城市不会去重（同一景点可能出现在不同城市列表中）。

### 9.5 JavaScript 语法注意

- JS 代码中不能使用中文引号（`""`），必须使用英文引号
- Unicode 字符使用 `\uXXXX` 转义（如 `\u514d\u8d39` = "免费"）
- 正则表达式中的 `/` 在 Python 字符串中可能触发 SyntaxWarning，不影响功能

### 9.6 subprocess 环境问题

- `shell=True` 在 Windows 上使用 `cmd.exe`，不支持 PowerShell 语法
- `PYTHONPATH` 必须显式设置，否则 `python -m browser_harness.run` 找不到模块
- 项目 venv 的 Python（3.11）与系统 Python（3.14）不同，browser-harness 必须用系统 Python 运行

---

## 十、数据清理

如果数据库中存在旧的假数据（分类标签如"赛事"、"自然山水"等），需要清理：

```python
from travel.models import Attraction

FAKE_PATTERNS = [
    '赛事', '自然山水', '博物馆&展馆', '城市漫步', '历史建筑',
    '地标观景', '夜游观景', '遛娃宝藏地', '赏花胜地', '海滨玩水',
    '度假村', '亲近动物', '游艇帆船', '跳伞', '缆车索道',
    '主题乐园&游乐场', '古镇古村', '漂流', '水上乐园&水族馆',
    '登高爬山', '泡温泉', '乘船游览', '展览', '演唱会', '科技馆',
    '亲水乐园', '清凉漂流', '动物园&水族馆', '水上乐园&水世界',
]

to_delete = []
for a in Attraction.objects.all():
    for p in FAKE_PATTERNS:
        if a.name.strip() == p or a.name.strip().startswith(p):
            to_delete.append(a.id)
            break

Attraction.objects.filter(id__in=to_delete).delete()
```

---

## 十一、图片高清优化

### 11.1 问题原因

携程 CDN 图片 URL 中包含尺寸参数，如 `_C_220_140.jpg` 表示 220×140 像素的缩略图。
直接在小尺寸缩略图上放大显示，会导致图片模糊。

### 11.2 携程 CDN 尺寸参数

| 前缀 | 含义 | 示例 |
|------|------|------|
| `_C` | 居中裁剪 (Crop) | `_C_220_140.jpg` |
| `_R` | 等比缩放 (Resize) | `_R_800_600.jpg` |
| `_W` | 带水印 (Watermark) | `_W_800_600.jpg` |

### 11.3 解决方案

**方案 A：Django Template Filter（推荐，运行时动态转换）**

文件：`travel/templatetags/image_filters.py`

提供两个 filter：
- `|hd` — 默认转为 800×600 等比缩放
- `|banner_hd` — 默认转为 1200×600 宽幅

模板用法：
```html
{% load image_filters %}

<!-- 景点卡片：600×400 -->
<img src="{{ attraction.image|hd:"600_400" }}">

<!-- 详情页大图：800×600 -->
<img src="{{ attraction.image|hd:"800_600" }}">

<!-- 轮播 Banner：1200×600 -->
<img src="{{ attraction.banner_url|banner_hd }}">
```

**方案 B：爬虫入库时直接存高清 URL**

`scrape_ctrip_real.py` 中的 `ctrip_image_hd()` 函数在入库时将缩略图 URL 转为高清：
- `image` 字段存 `_R_800_600`（800×600）
- `banner_url` 字段存 `_R_1200_600`（1200×600）

两种方案同时生效，确保任何来源的图片都能高清显示。

### 11.4 已更新的模板

| 模板 | 修改内容 |
|------|----------|
| `attraction_list.html` | 卡片图片 `|hd:"600_400"` |
| `attraction_detail.html` | 详情大图 `|hd:"800_600"`，banner `|banner_hd`，高德地图展示位置 |
| `home.html` | 轮播 `|banner_hd`，景区推荐卡片 `|hd:"600_400"` |
| `guide_detail.html` | 关联景点 `|hd:"600_400"` |

### 11.5 携程 CDN 支持的尺寸

| 尺寸 | 状态 | 用途 |
|------|------|------|
| `_R_800_600` | ✅ 200 | 详情页大图 |
| `_R_600_400` | ✅ 200 | 卡片缩略图 |
| `_R_960_540` | ✅ 200 | 轮播图 |
| `_R_1200_800` | ✅ 200 | Banner |
| `_R_1200_600` | ❌ 400 | **不支持！** |
| `_R_1000_700` | ❌ 400 | **不支持！** |

---

## 十二、经纬度补充

### 12.1 重要性

景点经纬度是 AI 路线规划的核心数据。没有经纬度，LangGraph Agent 无法计算景点间距离、调用高德路径规划 API、生成合理的行程路线。

### 12.2 补充方式

使用高德地理编码 API，根据 `景点名称 + 城市名` 获取经纬度：

```python
import requests

AMAP_KEY = '你的高德Web服务Key'

def geocode(address, city=''):
    r = requests.get('https://restapi.amap.com/v3/geocode/geo', params={
        'key': AMAP_KEY, 'address': address, 'city': city,
    }, timeout=10)
    data = r.json()
    if data.get('status') == '1' and data.get('geocodes'):
        loc = data['geocodes'][0]['location']  # "经度,纬度"
        lng, lat = loc.split(',')
        return float(lng), float(lat)
    return None, None
```

### 12.3 城市名修复

携程爬取的数据中城市名经常错位（如北京的景点被分到昆明），需要根据景点名称中的关键词推断正确城市。

### 12.4 详情页地图

景点详情页已集成高德地图 JS API，展示景点位置标记和信息窗口。需要配置系统环境变量 `gaodeMap` 为高德 JS API Key。

---

## 十三、扩展：爬取景点详情页

当前脚本只爬取列表页数据。如需爬取详情页（获取介绍、开放时间、图片等），可扩展：

```
new_tab("https://you.ctrip.com/sight/beijing1/s229.html")
wait_for_load(timeout=20)
time.sleep(5)
data = js("""(function() {
    var desc = document.querySelector('.moduleIntroDescription');
    var openTime = document.querySelector('.openTime');
    return JSON.stringify({
        description: desc ? desc.innerText : '',
        openTime: openTime ? openTime.innerText : ''
    });
})()""")
```

---

## 十四、图片加载错误处理

### 14.1 问题原因

景点图片来源多样（携程CDN、高德POI、用户上传等），可能出现以下加载失败情况：
- 携程CDN图片URL失效或尺寸参数不支持（返回400）
- 高德POI图片链接过期
- 数据库中image/banner_url字段为空字符串
- 网络超时或CDN节点故障

### 14.2 解决方案：前端 onerror 兜底

所有展示景点图片的 `<img>` 标签统一添加 `onerror` 事件，加载失败时显示 placehold.co 动态占位图：

```html
<img src="{{ attraction.image|hd:"600_400" }}" alt="{{ attraction.name }}"
     onerror="this.onerror=null;this.src='https://placehold.co/600x400/e2e8f0/64748b?text={{ attraction.name }}';">
```

**关键点**：
- `this.onerror=null` — 防止占位图也加载失败时无限循环
- 占位图尺寸与原图一致，避免布局抖动
- 占位图显示景点名称，用户仍可识别内容
- 配色 `e2e8f0/64748b`（浅灰底/深灰字）与项目 UI 风格一致

### 14.3 各页面占位图尺寸

| 页面 | 图片用途 | 原图尺寸 | 占位图尺寸 |
|------|----------|----------|------------|
| 首页轮播 | Banner大图 | 960×540 | 960×540 |
| 首页推荐卡片 | 景点缩略图 | 600×400 | 600×400 |
| 景点列表页 | 景点缩略图 | 600×400 | 600×400 |
| 景点详情页 | Banner大图 | 800×600 | 800×600 |
| 攻略详情页 | 关联景点缩略图 | 600×400 | 600×400 |

### 14.4 已更新的模板

| 模板文件 | 修改内容 |
|----------|----------|
| `accounts/home.html` | 轮播图 +onerror (960×540)，推荐卡片 onerror 从 `display:none` 改为占位图 (600×400) |
| `travel/attraction_list.html` | 卡片图片 +onerror (600×400) |
| `travel/attraction_detail.html` | Banner图片 +onerror (800×600) |
| `guides/guide_detail.html` | 关联景点图片 +onerror (600×400) |

### 14.5 后端数据修复脚本

配合前端兜底，后端也进行了数据清洗：

| 脚本 | 功能 |
|------|------|
| `_fix_images.py` | 将 image/banner_url 的 NULL 值更新为空字符串 |
| `_fill_images.py` | 调用高德POI搜索API，为无图片景点补充图片URL |

---

## 十五、当前数据状态

- 总景点数：279 条（真实数据，全部有经纬度）
- 覆盖城市：25 个
- 假数据已全部清理
- 城市名错误已修复（携程数据错位问题）
- 非景区数据已删除（演唱会、演出、境外景点等）
- 图片已全部转为高清 URL（image: 800×600, banner: 1200×800）
- 经纬度已通过高德地理编码 API 补充
- 详情页已集成高德地图展示景点位置
- **所有页面图片已添加 onerror 兜底处理**