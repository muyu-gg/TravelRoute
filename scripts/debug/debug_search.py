"""功能说明：调试景点搜索功能。"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

from travel.models import Attraction

print("=" * 60)
print("🔍 数据库调试工具")
print("=" * 60)

# 1. 检查总数据量
total = Attraction.objects.count()
print(f"\n📊 数据库总景点数: {total}")

# 2. 检查北京景点
beijing_attractions = Attraction.objects.filter(city_name__icontains='北京')
print(f"\n🏙️ 北京景点数量: {beijing_attractions.count()}")

if beijing_attractions.exists():
    print("\n北京景点列表:")
    for idx, attr in enumerate(beijing_attractions, 1):
        print(f"  {idx}. {attr.name}")
        print(f"     - ID: {attr.id}")
        print(f"     - Tags: '{attr.tags}'")
        print(f"     - Area: '{attr.area}'")
        print(f"     - is_advertisement: {attr.is_advertisement}")
        print(f"     - is_free: {attr.is_free}")
        print()

# 3. 测试搜索功能
print("=" * 60)
print("🧪 测试搜索功能")
print("=" * 60)

test_cases = [
    {"city": "北京", "preferences": "美食,景点", "budget": "20000"},
    {"city": "北京", "preferences": "景点", "budget": "高预算"},
    {"city": "北京", "preferences": "", "budget": "20000"},
    {"city": "三亚", "preferences": "海滨", "budget": "1000"},
]

from planner.agent.utils.attraction_repository import find_candidate_attractions

for test in test_cases:
    print(f"\n📍 测试: 城市={test['city']}, 偏好={test['preferences']}, 预算={test['budget']}")
    try:
        results = find_candidate_attractions(
            city=test['city'],
            preferences=test['preferences'],
            budget=test['budget'],
            limit=8
        )
        print(f"   ✅ 找到 {len(results)} 个景点:")
        for r in results[:3]:
            print(f"      - {r['name']} (tags: '{r['tags']}')")
        if len(results) > 3:
            print(f"      ... 还有 {len(results)-3} 个")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

print("\n" + "=" * 60)
print("✅ 调试完成")
print("=" * 60)