"""功能说明：调试 build_route_candidates 工具。"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

from planner.agent.utils.attraction_repository import find_candidate_attractions
from planner.agent.utils.route_utils import build_route_stops, rank_candidate_dicts
from planner.agent.utils.json_utils import dump_json, load_json_dict

print("=" * 70)
print("🔧 路线构建工具调试")
print("=" * 70)

# 1. 测试搜索景点
print("\n📍 步骤1: 搜索北京景点")
city = "北京"
preferences = "美食,景点"
budget = "20000"

attractions = find_candidate_attractions(
    city=city,
    preferences=preferences,
    budget=budget,
    limit=16
)

print(f"   找到 {len(attractions)} 个候选景点:")
for idx, attr in enumerate(attractions[:5], 1):
    print(f"     {idx}. {attr['name']} (tags: '{attr['tags']}', score: {attr['score']})")

# 2. 测试 rank_candidate_dicts
print("\n📍 步骤2: 排序候选景点")
ranked = rank_candidate_dicts(attractions, preferences, budget)
print(f"   排序后: {len(ranked)} 个景点")
if ranked:
    print(f"     第1名: {ranked[0]['name']}")

# 3. 测试 build_route_stops
print("\n📍 步骤3: 构建路线站点")
travel_time = "3天"

route_stops = build_route_stops(
    candidates=attractions,
    travel_time=travel_time,
    budget=budget,
    preferences=preferences,
)

print(f"   生成的路线站点数: {len(route_stops)}")

if route_stops:
    print("\n   📋 路线站点列表:")
    for stop in route_stops:
        print(f"      Day {stop['day_index']}-{stop['sequence']}: {stop['name']}")
else:
    print("   ❌ 路线站点为空！开始诊断...")

    # 诊断1：检查输入数据
    print("\n   🔍 诊断信息:")
    print(f"      - 输入候选数: {len(attractions)}")
    print(f"      - 排序后候选数: {len(ranked)}")

    if attractions:
        # 检查经纬度
        has_coords = sum(1 for a in attractions if a.get('longitude') and a.get('latitude'))
        print(f"      - 有经纬度的景点: {has_coords}/{len(attractions)}")

        # 检查第一个景点的详细信息
        sample = attractions[0]
        print(f"\n   📊 样本景点详情:")
        for key, value in sample.items():
            print(f"      {key}: {value}")

# 4. 模拟完整的 build_route_candidates 工具调用
print("\n" + "=" * 70)
print("🧪 模拟完整工具调用流程")
print("=" * 70)

from planner.agent.tools import build_route_candidates

attractions_json = dump_json({'attractions': attractions, 'count': len(attractions)})
print(f"\n attractions_json 长度: {len(attractions_json)} 字符")

try:
    result = build_route_candidates(
        attractions_json=attractions_json,
        travel_time=travel_time,
        budget=budget,
        preferences=preferences
    )
    result_dict = json.loads(result)
    print(f"\n✅ 工具返回结果:")
    print(f"   route_stops 数量: {result_dict.get('count', 0)}")

    if result_dict.get('route_stops'):
        print(f"\n   📍 路线站点:")
        for stop in result_dict['route_stops'][:5]:
            print(f"      - Day{stop['day_index']}-{stop['sequence']}: {stop['name']}")
    else:
        print(f"   ❌ 返回空路线！")

except Exception as e:
    print(f"\n❌ 工具调用失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试边界情况
print("\n" + "=" * 70)
print("🔬 边界情况测试")
print("=" * 70)

test_cases = [
    {"candidates": [], "desc": "空候选列表"},
    {"candidates": [attractions[0]] if attractions else [], "desc": "单个候选"},
]

for test in test_cases:
    print(f"\n测试: {test['desc']}")
    try:
        stops = build_route_stops(
            candidates=test['candidates'],
            travel_time="3天",
            budget="20000",
            preferences="美食"
        )
        print(f"   结果: {len(stops)} 个站点")
    except Exception as e:
        print(f"   错误: {e}")

print("\n" + "=" * 70)
print("✅ 调试完成")
print("=" * 70)