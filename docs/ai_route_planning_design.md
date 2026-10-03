# AI 旅游规划助手 · 定位与路线规划技术方案

> 场景：AI 旅游规划助手需要「获取/输入位置 → 规划最优路线 → 给出地铁/公交线路」。
> 技术栈：原生 Django（后端代理）+ Tailwind CDN（前端）+ 高德地图 Web 服务 API / JS API。
> 本文档覆盖：位置获取、公交/地铁线路获取、路线优化、所需工具、最小调用链、代码示例与合规注意事项。

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│  前端（Django 模板 + Tailwind + 高德 JS API）                 │
│  ① 一键定位 / 手动输入地址 / 输入经纬度                        │
│  ② 渲染地图、画路线 polyline、标注站点                         │
└───────────────▲─────────────────────────────────────────────┘
                │ 只调自己的 Django 接口（后端代理，保护 Key）
┌───────────────┴─────────────────────────────────────────────┐
│  Django 后端（视图做代理层）                                  │
│  ③ 地址 → 经纬度（地理编码）                                   │
│  ④ 经纬度 → 地址（逆地理编码）                                 │
│  ⑤ 多点排序优化（贪心/OR-Tools）                              │
│  ⑥ 调高德「公交路径规划」拿地铁/公交线路                       │
│  ⑦ 结果结构化后返回前端                                        │
└───────────────▲─────────────────────────────────────────────┘
                │ HTTPS（Key 放后端环境变量，绝不暴露前端）
┌───────────────┴─────────────────────────────────────────────┐
│  高德开放平台 Web 服务 API（restapi.amap.com）                │
└─────────────────────────────────────────────────────────────┘

（可选）AI 编排层：LLM / LangGraph Agent 通过 tool calling 调用上述能力
```

---

## 二、获取位置：三种方式组合使用

| 方式 | 接口 / 工具 | 精度 | 适用场景 |
| --- | --- | --- | --- |
| **浏览器实时定位** | 高德 JS API 的 `AMap.Geolocation` 插件（底层用浏览器 `navigator.geolocation`） | 街道级 | 一键「定位我当前位置」；**必须 HTTPS** |
| **IP 定位** | `GET https://restapi.amap.com/v5/ip?key={key}` | 城市级（约） | 用户拒绝授权时的降级方案 |
| **手动输入地址** | 地理编码 `GET https://restapi.amap.com/v3/geocode/geo` | 精确 | 用户在搜索框手输「北京 / 天安门」 |

拿到经纬度后如需回显「你在 XX 路附近」，再调**逆地理编码**（经纬度 → 结构化地址 + 周边 POI）。

### 2.1 地理编码（地址 → 经纬度）

```
GET https://restapi.amap.com/v3/geocode/geo
    ?key={key}
    &address=北京市朝阳区阜通东大街6号   # 也支持“天安门”这类地标名
    &city=北京                          # 可选，限定城市提高命中率
```

返回 `geocodes[0].location`，格式为字符串 `"116.480881,39.989410"`（经度在前）。

### 2.2 逆地理编码（经纬度 → 地址）

```
GET https://restapi.amap.com/v3/geocode/regeo
    ?key={key}
    &location=116.480881,39.989410
```

### 2.3 IP 定位

```
GET https://restapi.amap.com/v5/ip?key={key}&ip={可选}
```

### 2.4 浏览器实时定位（前端 JS API）

```html
<!-- 引入高德 JS API（需在平台申请 JS API Key + 安全密钥） -->
<script src="https://webapi.amap.com/maps?v=2.0&key={JS_API_KEY}"></script>
<script>
  AMap.plugin('AMap.Geolocation', function () {
    const geo = new AMap.Geolocation({
      enableHighAccuracy: true,
      timeout: 10000,
      buttonPosition: 'RB',
    });
    geo.getCurrentPosition();
    AMap.event.addListener(geo, 'complete', function (data) {
      // data.position: 经纬度；回传自己的后端接口
      console.log(data.position.lng, data.position.lat);
    });
    AMap.event.addListener(geo, 'error', function (err) {
      // 定位失败 → 降级到 IP 定位或让用户手动输入
    });
  });
</script>
```

> **Key 分两类，务必分开**：
> - **Web 服务 API Key**：后端调 `restapi.amap.com`，**必须保密**。
> - **JS API Key**：前端渲染地图 / 定位，需在控制台配置**安全密钥（数字签名）**。
> 不要把后端 Key 写进前端模板。

---

## 三、规划路线 + 地铁/公交线路：核心接口

### 3.1 公交路径规划（含地铁、公交换乘）

```
GET https://restapi.amap.com/v3/direction/transit/integrated
    ?key={key}
    &origin=116.68782,39.86099          # 起点：经度,纬度（最多6位小数）
    &destination=116.403414,39.924091   # 终点：经度,纬度
    &city=北京                          # 起点城市（跨城需再传 city2）
    &strategy=0                         # 换乘策略，见下表
```

**换乘策略 `strategy`（0–8）**

| 值 | 含义 |
| --- | --- |
| 0 | 推荐模式（综合权重，同高德 App 默认） |
| 1 | 最经济模式（票价最低） |
| 2 | 最少换乘模式 |
| 3 | 最少步行模式 |
| 4 | 最舒适模式（尽可能空调车） |
| 5 | **不乘地铁模式** |
| 6 | **地铁图模式**（起终点都是地铁站） |
| 7 | 地铁优先 |
| 8 | 时间最短 |

### 3.2 返回数据里直接含地铁/公交线路

公交路径规划返回的 `transits` → `segments` → `bus.buslines` 数组中，每个元素包含：

| 字段 | 含义 |
| --- | --- |
| `type` | 公交类型 → **「地铁线路」即在此区分** |
| `name` | 线路名，如 `445路(南十里居--地铁望京西站)`、`地铁1号线` |
| `departure_stop` | 上车站（含站名 + 站点 ID + 经纬度） |
| `arrival_stop` | 下车站（同上） |
| `distance` | 该段距离（米） |
| `duration` | 该段耗时（秒） |
| `polyline` | 该段路线坐标串，可直接画到地图 |
| `walking` | 每段步行距离、时间、方向引导（`instruction`） |

> **判断地铁还是公交**：读取 `buslines[].type`，或根据 `name` 是否含「地铁」关键词。**地铁图模式**用 `strategy=6`。

### 3.3 其他出行方式接口（同一套 Key）

| 方式 | 接口 |
| --- | --- |
| 驾车 | `https://restapi.amap.com/v5/direction/driving` |
| 步行 | `https://restapi.amap.com/v5/direction/walking` |
| 骑行 | `https://restapi.amap.com/v5/direction/bicycling` |
| 电动车 | `https://restapi.amap.com/v5/direction/electrobike` |
| 距离测量 | `https://restapi.amap.com/v3/distance`（type：0直线/1驾车/3步行） |

> **版本提醒**：公交/步行/驾车建议走 `v5/direction/...`（v5 公交新增策略 `6` 地铁图、`7` 地铁优先、`8` 时间短）；地理编码、POI 搜索等仍用 `v3`。旧 `v3` 骑行接口已不可用，必须用 `v4/v5`。

### 3.4 POI 搜索（选景点坐标更准）

```
GET https://restapi.amap.com/v3/place/text?key={key}&keywords=故宫&city=北京
GET https://restapi.amap.com/v3/place/around?key={key}&location={经度,纬度}&keywords=酒店&radius=1000
```

---

## 四、「规划最好的路线」怎么做

高德只负责**两点之间**的最优路线。要「规划最好的多景点路线」，需自己优化：

1. **意图解析**：LLM 把「北京 3 天、预算 1000、历史古迹」解析成结构化参数（目的地 / 天数 / 预算 / 偏好）。
2. **候选景点**：POI 搜索 + 你自己的景点库，为每个景点获取经纬度。
3. **路径优化**：用**贪心最近邻 / 2-opt / OR-Tools（TSP）** 对每天要去的景点排序，得到「距离比率最优」的访问顺序。
4. **分段规划**：对优化后的顺序，**逐段**调用公交路径规划接口，串成完整行程。
5. **回写结论**：把「距离比率 1.0、无往返折返」等校验结果返回给用户。

> 这与截图里 LangGraph 流程一致：`parse_travel_intent` → `search_attractions` → 路线规划 → `route_check`。可把「地理编码 / 路线规划 / POI 搜索」注册为 LangGraph 的**工具节点**，由 LLM 决定调用哪个。

---

## 五、需要哪些工具 / 组件

1. **高德开放平台账号**：创建应用，申请两类 Key（Web 服务 + JS API），关注每天免费配额与并发限制（Web 服务通常 5000 次/天）。
2. **后端 HTTP 客户端**：Django 中用 `requests` 或 `httpx` 封装高德调用；Key 放环境变量；统一封装超时、重试、结果缓存，避免重复计费。
3. **地图渲染**：前端引入高德 **JS API**，用返回的 `polyline` 画线、对站点打标记；或退一步用**静态地图 API** 只出图。
4. **Django 代理层**：视图做「接收条件 → 调高德 → 返回 JSON」，前端不直连高德、不暴露 Key。
5. **AI 编排层（可选）**：LLM / LangGraph 做意图解析 + function calling 调用地图工具。
6. **路径优化库（可选）**：`ortools`、`networkx`，或自写贪心最近邻。
7. **坐标系注意**：高德用 **GCJ-02（火星坐标系）**，与 GPS 的 WGS-84 存在偏移；若来源是 GPS/百度坐标，需先做坐标转换。
8. **合规与隐私**：定位需用户授权；说明用途；遵守地图数据合规要求，`key` 与安全密钥妥善保管。

---

## 六、最小可用调用链

```
手动输入 / 定位获取起点
  → 地理编码：把「北京」等文字变成经纬度
  → 公交路径规划 transit/integrated（strategy=0/2/7）→ 拿到地铁 + 公交 + 换乘 + 步行段
  → 解析 buslines.type 判断地铁还是公交，格式化输出
  → 前端 JS API 用 polyline 画线、标记站点
```

---

## 七、Django 调用示例代码

### 7.1 封装高德客户端 `services/amap.py`

```python
import os
import requests

AMAP_KEY = os.environ.get("AMAP_WEB_KEY", "")


def _get(path: str, params: dict) -> dict:
    params = {**params, "key": AMAP_KEY}
    resp = requests.get(f"https://restapi.amap.com{path}", params=params, timeout=8)
    resp.raise_for_status()
    return resp.json()


def geocode(address: str, city: str = "") -> str | None:
    """地址 → "经度,纬度" """
    data = _get("/v3/geocode/geo", {"address": address, "city": city})
    if data.get("status") == "1" and data.get("geocodes"):
        return data["geocodes"][0]["location"]
    return None


def regeo(location: str) -> str | None:
    """"经度,纬度" → 结构化地址"""
    data = _get("/v3/geocode/regeo", {"location": location})
    if data.get("status") == "1":
        return data["regeocode"]["formatted_address"]
    return None


def transit_route(origin: str, destination: str, city: str, strategy: int = 0) -> dict:
    """公交/地铁/综合换乘路径规划"""
    return _get("/v3/direction/transit/integrated", {
        "origin": origin,
        "destination": destination,
        "city": city,
        "strategy": strategy,
    })


def parse_transit_lines(route_json: dict) -> list[dict]:
    """从高德返回中提炼地铁/公交线路。"""
    result = []
    transits = route_json.get("route", {}).get("transits", [])
    for plan in transits:
        segs = []
        for seg in plan.get("segments", []):
            bus = seg.get("bus", {})
            for line in bus.get("buslines", []):
                segs.append({
                    "is_metro": "地铁" in (line.get("type") or "") or "地铁" in (line.get("name") or ""),
                    "line_name": line.get("name"),
                    "from_stop": bus.get("departure_stop", {}).get("name"),
                    "to_stop": bus.get("arrival_stop", {}).get("name"),
                    "distance_m": line.get("distance"),
                    "duration_s": line.get("duration"),
                    "polyline": line.get("polyline"),
                })
            if seg.get("walking"):
                w = seg["walking"]
                segs.append({
                    "is_metro": False,
                    "line_name": "步行",
                    "distance_m": w.get("distance"),
                    "duration_s": w.get("duration"),
                    "polyline": w.get("polyline"),
                })
        result.append({
            "duration_s": plan.get("duration"),
            "cost": plan.get("cost"),
            "segments": segs,
        })
    return result
```

### 7.2 视图 `views.py`

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .services import amap


@require_POST
def api_plan_route(request):
    """前端提交起点/终点 → 后端代理调高德 → 返回结构化路线。"""
    origin = request.POST.get("origin", "").strip()          # "经度,纬度"
    destination = request.POST.get("destination", "").strip()
    city = request.POST.get("city", "").strip()
    strategy = int(request.POST.get("strategy", 0))

    # 若前端传的是地址文字，先做地理编码
    if origin and "," not in origin:
        origin = amap.geocode(origin, city) or ""
    if destination and "," not in destination:
        destination = amap.geocode(destination, city) or ""

    if not origin or not destination:
        return JsonResponse({"ok": False, "msg": "起点或终点无法解析"}, status=400)

    raw = amap.transit_route(origin, destination, city, strategy)
    return JsonResponse({"ok": True, "plans": amap.parse_transit_lines(raw)})
```

### 7.3 前端提交（Django 模板片段）

```html
<form id="routeForm" method="post" action="{% url 'api_plan_route' %}">
  {% csrf_token %}
  <input name="origin" placeholder="起点，如：北京站" class="...">
  <input name="destination" placeholder="终点，如：故宫" class="...">
  <input name="city" placeholder="城市，如：北京" class="...">
  <button type="submit" class="...">生成路线</button>
</form>
```

---

## 八、接口速查表

| 功能 | 方法与 URL |
| --- | --- |
| 地理编码 | `GET https://restapi.amap.com/v3/geocode/geo` |
| 逆地理编码 | `GET https://restapi.amap.com/v3/geocode/regeo` |
| IP 定位 | `GET https://restapi.amap.com/v5/ip` |
| POI 关键字搜索 | `GET https://restapi.amap.com/v3/place/text` |
| POI 周边搜索 | `GET https://restapi.amap.com/v3/place/around` |
| 公交/地铁路径规划 | `GET https://restapi.amap.com/v3/direction/transit/integrated` |
| 驾车路径规划 | `GET https://restapi.amap.com/v5/direction/driving` |
| 步行路径规划 | `GET https://restapi.amap.com/v5/direction/walking` |
| 骑行路径规划 | `GET https://restapi.amap.com/v4/direction/bicycling` |
| 距离测量 | `GET https://restapi.amap.com/v3/distance` |
| 行政区划编码 | `GET https://restapi.amap.com/v3/config/district` |
| 天气查询 | `GET https://restapi.amap.com/v3/weather/weatherInfo` |

---

## 九、合规与注意事项

- 定位属敏感权限：**必须先获取用户授权**，说明用途，并提供「手动输入」降级路径。
- `key` 与安全密钥不得硬编码进前端或提交到仓库，放环境变量 / 密钥管理。
- 高德使用 **GCJ-02** 坐标系，跨坐标系数据需转换。
- 关注免费配额与并发限制，做好缓存与错误降级。

---

> 参考来源：高德开放平台官方 API 文档（公交路径规划 `transit/integrated`、路线规划概述、JS API 定位插件、地理/逆地理编码）。
> 说明：本文档为通用技术开发参考，不构成任何投资建议。金融市场存在风险，相关决策请独立判断并自行承担风险。
