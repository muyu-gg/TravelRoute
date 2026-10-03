import os
import sys
import re
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
sys.path.insert(0, BASE_DIR)

import django
django.setup()

from travel.models import Attraction

BAD_NAMES = re.compile(
    r'^(赏花|遛娃|夜游|亲近|缆车|玩水|避暑|冬季|空中|温泉|泡汤|水上|户外|休闲|娱乐|主题|乐园|展览|展馆|踏青|滑雪|动植|体验|观光|名胜|自然|购物|美食|住宿|度假|当地|跟团|自由|定制|邮轮|一日|租车|社区|地图|金融|企业|老友|礼品|全球|攻略|搜索|位置|类型|排序|只看|可订|免费|特色|必打|亲子|赏秋|赏花胜地|遛娃宝藏地|夜游观景|亲近动物|缆车索道)$'
)

all_attractions = Attraction.objects.all().order_by('city_name', '-score')
total = all_attractions.count()
print(f"当前总数: {total}")

bad_count = 0
for a in all_attractions:
    if BAD_NAMES.match(a.name) or len(a.name) < 2 or a.name == a.city_name:
        a.delete()
        bad_count += 1

print(f"删除无效名称: {bad_count} 条")

remaining = list(Attraction.objects.all().order_by('city_name', '-score'))
print(f"剩余: {len(remaining)} 条")

target = len(remaining) // 2
to_delete = len(remaining) - target

cities = {}
for a in remaining:
    cities.setdefault(a.city_name, []).append(a)

print(f"\n各城市数据:")
for city, attrs in sorted(cities.items()):
    print(f"  {city}: {len(attrs)} 条")

delete_ids = set()
for city, attrs in cities.items():
    keep = max(1, len(attrs) // 2)
    attrs_sorted = sorted(attrs, key=lambda x: x.score)
    for a in attrs_sorted[:len(attrs) - keep]:
        delete_ids.add(a.id)

print(f"\n计划删除: {len(delete_ids)} 条, 保留: {len(remaining) - len(delete_ids)} 条")

Attraction.objects.filter(id__in=delete_ids).delete()

final = Attraction.objects.all().order_by('city_name', '-score')
print(f"\n最终保留: {final.count()} 条")
print("\n保留数据:")
for city in cities:
    count = final.filter(city_name=city).count()
    if count > 0:
        print(f"  {city}: {count} 条")

print("\n更新图片URL...")
updated = 0
for a in final:
    if not a.image:
        a.image = f"https://you.ctrip.com/sight/{a.city_name}/{a.name}"
        a.save(update_fields=['image'])
        updated += 1

print(f"更新了 {updated} 条图片字段（占位URL）")