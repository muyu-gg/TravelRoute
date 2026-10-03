"""功能说明：综合数据填充脚本 - 补充景点图片URL、创建用户、创建攻略。"""
import os
import sys
import django
import random
import hashlib
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from django.contrib.auth import get_user_model
from travel.models import Attraction
from guides.models import TravelGuide, TravelGuideAttraction

User = get_user_model()

print("=" * 70)
print("[SEED] Comprehensive Data Seeding Script")
print("=" * 70)


# ============================================================
# PART 1: 补充景点图片URL和经纬度
# ============================================================
print("\n[PART 1] Updating Attraction Image URLs & Coordinates")
print("-" * 70)

CITY_COORDS = {
    '三亚': {'lng': 109.50, 'lat': 18.25, 'center_lng': 109.50, 'center_lat': 18.25},
    '上海': {'lng': 121.47, 'lat': 31.23, 'center_lng': 121.47, 'center_lat': 31.23},
    '丽江': {'lng': 100.23, 'lat': 26.87, 'center_lng': 100.23, 'center_lat': 26.87},
    '南京': {'lng': 118.78, 'lat': 32.06, 'center_lng': 118.78, 'center_lat': 32.06},
    '厦门': {'lng': 118.09, 'lat': 24.48, 'center_lng': 118.09, 'center_lat': 24.48},
    '哈尔滨': {'lng': 126.63, 'lat': 45.75, 'center_lng': 126.63, 'center_lat': 45.75},
    '大连': {'lng': 121.62, 'lat': 38.91, 'center_lng': 121.62, 'center_lat': 38.91},
    '天津': {'lng': 117.19, 'lat': 39.13, 'center_lng': 117.19, 'center_lat': 39.13},
    '广州': {'lng': 113.26, 'lat': 23.13, 'center_lng': 113.26, 'center_lat': 23.13},
    '北京': {'lng': 116.40, 'lat': 39.90, 'center_lng': 116.40, 'center_lat': 39.90},
    '成都': {'lng': 104.07, 'lat': 30.57, 'center_lng': 104.07, 'center_lat': 30.57},
    '杭州': {'lng': 120.15, 'lat': 30.28, 'center_lng': 120.15, 'center_lat': 30.28},
    '西安': {'lng': 108.94, 'lat': 34.26, 'center_lng': 108.94, 'center_lat': 34.26},
    '重庆': {'lng': 106.55, 'lat': 29.56, 'center_lng': 106.55, 'center_lat': 29.56},
    '青岛': {'lng': 120.38, 'lat': 36.07, 'center_lng': 120.38, 'center_lat': 36.07},
    '苏州': {'lng': 120.62, 'lat': 31.30, 'center_lng': 120.62, 'center_lat': 31.30},
    '长沙': {'lng': 112.98, 'lat': 28.19, 'center_lng': 112.98, 'center_lat': 28.19},
    '武汉': {'lng': 114.30, 'lat': 30.59, 'center_lng': 114.30, 'center_lat': 30.59},
    '深圳': {'lng': 114.06, 'lat': 22.54, 'center_lng': 114.06, 'center_lat': 22.54},
}

TAG_MAPPING = {
    '遛娃宝藏地': '亲子,遛娃,家庭',
    '赏花胜地': '赏花,自然,拍照',
    '夜游观景': '夜景,观景,浪漫',
    '缆车索道': '缆车,索道,观景',
    '亲近动物': '动物园,亲子,自然',
    '游艇帆船': '游艇,帆船,海上',
    '跳伞': '极限运动,跳伞,刺激',
    '度假村': '度假,休闲,温泉',
    '地标观景': '地标,观景,打卡',
    '海滨玩水': '海滨,玩水,沙滩',
    '赛事': '赛事,体育,观赛',
    '博物馆&展馆': '博物馆,文化,展览',
    '自然山水': '自然,山水,徒步',
    '主题乐园&游乐场': '乐园,游乐,亲子',
    '美食': '美食,小吃,特色',
}

IMAGE_URLS = {
    '遛娃宝藏地': 'https://dimg04.c-ctrip.com/images/100s0h000000c8g72E398_C_500_300.jpg',
    '赏花胜地': 'https://dimg04.c-ctrip.com/images/100o0h000000c8h76F6A4_C_500_300.jpg',
    '夜游观景': 'https://dimg04.c-ctrip.com/images/100s0h000000c8g93F5B2_C_500_300.jpg',
    '缆车索道': 'https://dimg04.c-ctrip.com/images/100i0h000000c8g54D7C1_C_500_300.jpg',
    '亲近动物': 'https://dimg04.c-ctrip.com/images/100s0h000000c8g15C8A3_C_500_300.jpg',
    '游艇帆船': 'https://dimg04.c-ctrip.com/images/100s0h000000c8h26D9B4_C_500_300.jpg',
    '跳伞': 'https://dimg04.c-ctrip.com/images/100o0h000000c8h37E0C5_C_500_300.jpg',
    '度假村': 'https://dimg04.c-ctrip.com/images/100s0h000000c8h48F1D6_C_500_300.jpg',
    '地标观景': 'https://dimg04.c-ctrip.com/images/100i0h000000c8h59A2E7_C_500_300.jpg',
    '海滨玩水': 'https://dimg04.c-ctrip.com/images/100s0h000000c8h6AB3F8_C_500_300.jpg',
    '赛事': 'https://dimg04.c-ctrip.com/images/100o0h000000c8h7BC4G9_C_500_300.jpg',
    '博物馆&展馆': 'https://dimg04.c-ctrip.com/images/100s0h000000c8h8CD5H0_C_500_300.jpg',
    '自然山水': 'https://dimg04.c-ctrip.com/images/100i0h000000c8h9DE6I1_C_500_300.jpg',
    '主题乐园&游乐场': 'https://dimg04.c-ctrip.com/images/100s0h000000c8h0EF7J2_C_500_300.jpg',
    '美食': 'https://dimg04.c-ctrip.com/images/100o0h000000c8i1FG8K3_C_500_300.jpg',
}

DEFAULT_IMAGE = 'https://dimg04.c-ctrip.com/images/100s0h000000c8g72E398_C_500_300.jpg'

attractions = Attraction.objects.all()
updated_count = 0

for attr in attractions:
    changed = False

    if not attr.image:
        attr.image = IMAGE_URLS.get(attr.name, DEFAULT_IMAGE)
        changed = True

    if not attr.tags:
        attr.tags = TAG_MAPPING.get(attr.name, '')
        changed = True

    city_info = CITY_COORDS.get(attr.city_name)
    if city_info and (attr.longitude == 0.0 or attr.latitude == 0.0):
        poi_hash = hashlib.md5(str(attr.poi_id).encode()).hexdigest()
        offset_lng = (int(poi_hash[:4], 16) % 100 - 50) * 0.002
        offset_lat = (int(poi_hash[4:8], 16) % 100 - 50) * 0.002
        attr.longitude = round(city_info['lng'] + offset_lng, 6)
        attr.latitude = round(city_info['lat'] + offset_lat, 6)
        changed = True

    if not attr.detail_url or attr.detail_url == 'https://you.ctrip.com/sight/':
        attr.detail_url = f'https://you.ctrip.com/sight/{attr.city_name}/{attr.poi_id}.html'
        changed = True

    if changed:
        attr.save(update_fields=['image', 'tags', 'longitude', 'latitude', 'detail_url'])
        updated_count += 1

print(f"  Updated {updated_count} attractions with image URLs, tags, coordinates, and detail URLs")

beijing_count = Attraction.objects.filter(city_name__icontains='北京').count()
beijing_with_coords = Attraction.objects.filter(city_name__icontains='北京').exclude(longitude=0.0).count()
print(f"  Beijing: {beijing_count} attractions, {beijing_with_coords} with valid coordinates")


# ============================================================
# PART 2: 创建测试用户
# ============================================================
print("\n[PART 2] Creating Test Users")
print("-" * 70)

test_users = [
    {'username': 'traveler_zhang', 'email': 'zhang@example.com', 'password': 'Zhang123456!',
     'first_name': '张', 'last_name': '旅行'},
    {'username': 'explorer_li', 'email': 'li@example.com', 'password': 'Li123456!',
     'first_name': '李', 'last_name': '探索'},
    {'username': 'wanderer_wang', 'email': 'wang@example.com', 'password': 'Wang123456!',
     'first_name': '王', 'last_name': '漫游'},
    {'username': 'adventurer_zhao', 'email': 'zhao@example.com', 'password': 'Zhao123456!',
     'first_name': '赵', 'last_name': '冒险'},
    {'username': 'sightseer_chen', 'email': 'chen@example.com', 'password': 'Chen123456!',
     'first_name': '陈', 'last_name': '观光'},
]

created_users = []
for user_data in test_users:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults={
            'email': user_data['email'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'is_active': True,
        }
    )
    if created:
        user.set_password(user_data['password'])
        user.save()
        created_users.append(user)
        print(f"  Created: {user.username} ({user.first_name}{user.last_name}) - password: {user_data['password']}")
    else:
        created_users.append(user)
        print(f"  Exists:  {user.username}")

if not created_users:
    created_users = list(User.objects.filter(is_active=True, is_superuser=False)[:5])

print(f"  Total active users: {User.objects.filter(is_active=True).count()}")


# ============================================================
# PART 3: 创建旅游攻略
# ============================================================
print("\n[PART 3] Creating Travel Guides")
print("-" * 70)

GUIDE_DATA = [
    {
        'title': '北京3日深度游攻略：古都风韵与现代都市的完美融合',
        'city': '北京',
        'summary': '三天玩转北京！从故宫到长城，从胡同到CBD，感受千年古都的独特魅力。',
        'content': """## Day 1：皇城根下，穿越千年

### 上午：故宫博物院
- **建议时间**：8:30 - 12:00
- **门票**：60元（旺季），需提前网上预约
- **游览路线**：午门 → 太和殿 → 中和殿 → 保和殿 → 乾清宫 → 御花园 → 神武门
- **Tips**：建议从东华门进，避开人流高峰；租一个电子讲解器，了解每座宫殿背后的故事

### 下午：景山公园 + 南锣鼓巷
- **景山公园**：从万春亭俯瞰故宫全景，拍照绝佳位置
- **南锣鼓巷**：逛胡同、品小吃，推荐文宇奶酪店和吉事果
- **Tips**：南锣鼓巷人流量大，建议下午4点后前往

### 晚上：簋街美食
- **推荐餐厅**：花家怡园（烤鸭）、金簋小山城（火锅）
- **人均消费**：80-150元

---

## Day 2：长城壮歌，奥运荣光

### 上午：慕田峪长城
- **建议时间**：7:00 - 12:00（含往返车程）
- **交通**：东直门乘916快到怀柔，转乘H23路
- **门票**：40元，缆车单程100元
- **Tips**：比八达岭人少，风景更美；建议坐缆车上、步行下

### 下午：鸟巢 + 水立方
- **外观拍照**即可，不建议买票入内
- **周边**：奥林匹克森林公园，免费，适合散步

### 晚上：三里屯
- 北京最时尚的商圈，酒吧、餐厅、购物一站式体验

---

## Day 3：文化之旅，慢享北京

### 上午：颐和园
- **建议时间**：8:00 - 12:00
- **门票**：30元（联票60元含苏州街等）
- **必看**：长廊、佛香阁、十七孔桥、昆明湖
- **Tips**：从北宫门进，东宫门出，游览路线最顺

### 下午：798艺术区
- 免费开放，各种画廊、咖啡馆、创意小店
- 推荐UCCA尤伦斯当代艺术中心

### 晚上：前门大街 + 大栅栏
- 老北京风情街，全聚德烤鸭、都一处烧麦
- **人均消费**：100-200元

---

## 实用信息

| 项目 | 说明 |
|------|------|
| 交通 | 地铁最方便，办一张交通卡 |
| 住宿 | 建议住东城区或西城区，交通便利 |
| 预算 | 3天约2000-3000元/人（不含住宿） |
| 最佳季节 | 9-10月秋高气爽，最佳游览时间 |
""",
    },
    {
        'title': '三亚5天4晚海岛度假全攻略',
        'city': '三亚',
        'summary': '阳光、沙滩、海浪！一份超详细的三亚度假攻略，含住宿推荐和美食地图。',
        'content': """## Day 1：抵达三亚，初识椰城

- **入住酒店**：推荐亚龙湾或海棠湾区域
- **傍晚**：椰梦长廊散步，看三亚湾日落
- **晚餐**：第一市场海鲜，人均100元左右

## Day 2：亚龙湾一日游

- **上午**：亚龙湾沙滩戏水，被誉为"天下第一湾"
- **下午**：亚龙湾热带天堂森林公园，非诚勿扰2取景地
- **晚上**：亚龙湾奥特莱斯逛街

## Day 3：蜈支洲岛

- **全天**：乘船前往蜈支洲岛
- **推荐项目**：环岛观光车、潜水、海上摩托
- **Tips**：提前在网上买套票更划算

## Day 4：南山文化旅游区

- **上午**：南山寺，108米海上观音
- **下午**：天涯海角，打卡留念
- **晚上**：三亚千古情演出（推荐）

## Day 5：免税购物 + 返程

- **上午**：海棠湾免税店购物
- **下午**：返程

## 预算参考

| 项目 | 费用 |
|------|------|
| 住宿 | 300-800元/晚 |
| 餐饮 | 100-200元/天 |
| 景点 | 约500元/人 |
| 总计 | 约4000-6000元/人 |
""",
    },
    {
        'title': '上海周末2日游：魔都的摩登与怀旧',
        'city': '上海',
        'summary': '两天玩遍上海经典地标，从外滩到田子坊，从南京路到迪士尼，魔都魅力一网打尽。',
        'content': """## Day 1：经典上海

### 上午：外滩 + 南京路
- 外滩万国建筑群拍照，浦东天际线尽收眼底
- 南京路步行街逛街，永安百货、第一食品商店

### 下午：豫园 + 城隍庙
- 豫园门票40元，江南园林精品
- 城隍庙小吃：南翔小笼、蟹粉汤包

### 晚上：新天地
- 石库门里弄改造的时尚休闲区
- 推荐在湖畔酒吧小酌

## Day 2：文化体验

### 上午：上海博物馆
- 免费开放，青铜器和书画收藏国内顶尖

### 下午：田子坊 + 思南公馆
- 田子坊：文艺小店、手工艺品
- 思南公馆：法租界老洋房，露天咖啡

### 晚上：陆家嘴
- 上海中心大厦观光层（门票180元）
- 俯瞰整个上海夜景

## 美食推荐
- 生煎包：小杨生煎
- 本帮菜：上海老饭店
- 蟹粉：蟹尊苑
""",
    },
    {
        'title': '丽江3日慢旅行：在古城中寻找诗和远方',
        'city': '丽江',
        'summary': '远离都市喧嚣，在丽江古城漫步，在玉龙雪山仰望，在束河古镇发呆，找回内心的宁静。',
        'content': """## Day 1：丽江古城

- **上午**：大研古城，四方街、木府（门票40元）
- **下午**：万古楼登高望远，狮子山观古城全景
- **晚上**：酒吧街听民谣，或安静地坐在客栈院子里看星空
- **Tips**：古城维护费50元，住古城内可让客栈代买

## Day 2：玉龙雪山

- **全天**：玉龙雪山一日游
- **大索道**：直达4506米冰川公园，门票+索道约240元
- **蓝月谷**：下山后必去，水色如蓝宝石
- **Tips**：提前买好氧气瓶（20元/瓶），注意高反

## Day 3：束河古镇 + 白沙古镇

- **上午**：束河古镇，比大研更安静，适合发呆
- **下午**：白沙古镇，看白沙壁画，体验纳西文化
- **晚上**：返回大研古城，购买伴手礼

## 住宿推荐
- 大研古城内客栈：200-500元/晚
- 束河古镇客栈：150-300元/晚
""",
    },
    {
        'title': '厦门3日文艺之旅：在鹭岛遇见最美海岸线',
        'city': '厦门',
        'summary': '鼓浪屿的琴声、环岛路的海风、曾厝垵的文艺，厦门是一座来了就不想走的城市。',
        'content': """## Day 1：鼓浪屿

- **上午**：乘轮渡上岛（35元往返），日光岩（60元）俯瞰全岛
- **下午**：菽庄花园、皓月园，漫步万国建筑群
- **晚上**：岛上听钢琴演奏，或返回中山路逛街

## Day 2：厦大 + 环岛路

- **上午**：厦门大学（需预约），芙蓉湖、芙蓉隧道涂鸦
- **下午**：南普陀寺 → 胡里山炮台 → 环岛路骑行
- **晚上**：曾厝垵文创村，各种特色小店和美食

## Day 3：集美学村 + 返程

- **上午**：集美学村，嘉庚建筑群
- **下午**：八市（第八菜市场），最地道的厦门味道

## 必吃美食
- 沙茶面：乌糖沙茶面
- 海蛎煎：莲欢海蛎煎
- 花生汤：黄则和花生汤
- 土笋冻：八市里的小摊
""",
    },
    {
        'title': '哈尔滨冬季3日游：冰雪奇缘之旅',
        'city': '哈尔滨',
        'summary': '在冰城感受零下30度的热情！冰雪大世界、中央大街、圣索菲亚教堂，冬季哈尔滨美如童话。',
        'content': """## Day 1：中央大街 + 圣索菲亚

- **上午**：圣索菲亚教堂，拜占庭风格建筑，拍照打卡
- **下午**：中央大街步行街，马迭尔冰棍、秋林红肠
- **晚上**：防洪纪念塔看松花江夜景

## Day 2：冰雪大世界

- **全天**：冰雪大世界（门票约300元）
- **推荐项目**：冰滑梯、雪圈、冰上自行车
- **Tips**：穿厚！暖宝宝必备，手机注意保暖防关机

## Day 3：太阳岛 + 极地馆

- **上午**：太阳岛雪博会
- **下午**：哈尔滨极地馆，看白鲸表演
- **晚上**：老道外巴洛克街区，品尝锅包肉

## 冬季装备清单
- 羽绒服（-30度级别）
- 雪地靴 + 暖宝宝
- 保温杯
- 触屏手套
""",
    },
    {
        'title': '南京2日历史文化游：六朝古都的千年回响',
        'city': '南京',
        'summary': '中山陵的庄严肃穆、夫子庙的热闹繁华、明孝陵的古朴幽静，南京值得你慢慢品味。',
        'content': """## Day 1：钟山风景区

- **上午**：中山陵（免费，需预约），392级台阶登顶
- **下午**：明孝陵（70元），最美600年神道
- **晚上**：夫子庙 + 秦淮河夜游（画舫80元）

## Day 2：城市文化

- **上午**：南京博物院（免费，需预约），民国馆拍照超赞
- **下午**：总统府（40元）→ 1912街区
- **晚上**：老门东，南京大牌档品尝金陵美食

## 必吃美食
- 盐水鸭：韩复兴
- 鸭血粉丝汤：回味鸭血粉丝
- 小笼包：尹氏鸡汁汤包
- 牛锅贴：李记清真馆
""",
    },
    {
        'title': '广州美食3日游：食在广州，味在舌尖',
        'city': '广州',
        'summary': '早茶的精致、煲仔饭的烟火气、糖水的甜蜜，广州是一座用味蕾记住的城市。',
        'content': """## Day 1：老广州

- **早茶**：陶陶居或点都德，虾饺、烧卖、肠粉
- **上午**：陈家祠（10元），岭南建筑精华
- **下午**：沙面岛，欧式建筑群拍照
- **晚上**：上下九步行街，南信双皮奶

## Day 2：新广州

- **上午**：广东省博物馆（免费）→ 广州塔（150元）
- **下午**：花城广场 → 海心沙
- **晚上**：珠江夜游，看两岸灯光秀

## Day 3：番禺 + 返程

- **上午**：长隆野生动物世界（250元）
- **下午**：北京路逛街，购买手信

## 美食地图
- 早茶：陶陶居、点都德、广州酒家
- 煲仔饭：超记煲仔饭
- 糖水：百花甜品
- 云吞面：宝华面店
""",
    },
]

created_guides = []
for i, guide_data in enumerate(GUIDE_DATA):
    author = created_users[i % len(created_users)]

    guide, created = TravelGuide.objects.get_or_create(
        title=guide_data['title'],
        defaults={
            'author': author,
            'city': guide_data['city'],
            'summary': guide_data['summary'],
            'content': guide_data['content'],
            'view_count': random.randint(50, 500),
        }
    )

    if created:
        city_attractions = Attraction.objects.filter(
            city_name__icontains=guide_data['city'],
            is_advertisement=False,
        )[:5]

        for attr in city_attractions:
            TravelGuideAttraction.objects.get_or_create(
                guide=guide,
                attraction=attr,
            )

        created_guides.append(guide)
        print(f"  Created: [{guide.city}] {guide.title[:30]}... by {author.username}")
    else:
        created_guides.append(guide)
        print(f"  Exists:  [{guide.city}] {guide.title[:30]}...")

print(f"\n  Total guides: {TravelGuide.objects.count()}")


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("[DONE] Data Seeding Complete!")
print("=" * 70)

print(f"\n  Attractions updated: {updated_count}")
print(f"  Users created: {len([u for u in created_users if u])}")
print(f"  Guides created: {len(created_guides)}")

print(f"\n  Total attractions: {Attraction.objects.count()}")
print(f"  Total users: {User.objects.filter(is_active=True).count()}")
print(f"  Total guides: {TravelGuide.objects.count()}")

print("\n  User accounts (for testing):")
for ud in test_users:
    print(f"    username: {ud['username']}, password: {ud['password']}")

print("\n" + "=" * 70)