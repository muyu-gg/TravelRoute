"""功能说明：完整测试旅游规划流程。"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

from planner.agent.graph import run_route_planner, stream_route_planner

# 设置输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("[TEST] Complete Travel Planning Flow Test")
print("=" * 70)

# 测试参数
test_params = {
    'city': '北京',
    'budget': '20000',
    'travel_time': '3天',
    'preferences': '美食,景点'
}

print(f"\n📋 测试参数:")
for key, value in test_params.items():
    print(f"   {key}: {value}")

print("\n" + "-" * 70)
print("🔄 开始运行同步规划...")
print("-" * 70)

try:
    result = run_route_planner(**test_params)

    print(f"\n✅ 规划完成！")
    print(f"\n📊 结果摘要:")

    # 意图识别
    intent = result.get('intent', {})
    print(f"\n1️⃣  意图识别:")
    print(f"   城市: {intent.get('city', 'N/A')}")
    print(f"   天数: {intent.get('travel_days', 'N/A')}")
    print(f"   偏好: {intent.get('preferences', 'N/A')}")

    # 候选景点
    candidates = result.get('candidates', [])
    print(f"\n2️⃣  候选景点: {len(candidates)} 个")
    for idx, c in enumerate(candidates[:5], 1):
        print(f"   {idx}. {c.get('name', 'N/A')} (评分: {c.get('score', 0)})")

    # 路线站点（关键！）
    route_stops = result.get('route_stops', [])
    print(f"\n3️⃣  路线站点: {len(route_stops)} 个 ⭐")

    if route_stops:
        print("   📍 详细路线:")
        for stop in route_stops:
            day = stop.get('day_index', '?')
            seq = stop.get('sequence', '?')
            name = stop.get('name', 'N/A')
            print(f"      Day{day}-{seq}: {name}")
    else:
        print("   ❌ 路线站点为空！这是问题所在！")

    # 验证结果
    validation = result.get('validation_result', {})
    print(f"\n4️⃣  路线验证:")
    print(f"   是否有效: {validation.get('is_valid', False)}")
    print(f"   评分: {validation.get('score', 0)}")
    if validation.get('issues'):
        print(f"   问题: {validation.get('issues')}")

    # 最终方案
    final_plan = result.get('final_plan', '')
    print(f"\n5️⃣  最终方案长度: {len(final_plan)} 字符")
    if final_plan:
        print(f"\n📝 最终方案预览 (前200字):")
        print(f"   {final_plan[:200]}...")

    # 处理步骤
    steps = result.get('process_steps', [])
    print(f"\n📋 处理步骤 ({len(steps)} 步):")
    for idx, step in enumerate(steps, 1):
        title = step.get('title', '')
        desc = step.get('description', '')[:50]
        status = step.get('status', '')
        status_icon = {'success': '✅', 'running': '⏳', 'warning': '⚠️', 'failed': '❌'}.get(status, '❓')
        print(f"   {idx}. {status_icon} {title}: {desc}")

except Exception as e:
    print(f"\n❌ 规划失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ 测试完成")
print("=" * 70)

# 额外：检查数据质量
print("\n\n" + "=" * 70)
print("🔍 数据质量检查")
print("=" * 70)

from travel.models import Attraction

beijing_attractions = Attraction.objects.filter(city_name__icontains='北京')
print(f"\n北京景点数据质量:")

has_coords = 0
has_tags = 0
for attr in beijing_attractions:
    if attr.longitude and attr.latitude and attr.longitude != 0.0:
        has_coords += 1
    if attr.tags:
        has_tags += 1

print(f"   总数: {beijing_attractions.count()}")
print(f"   有有效经纬度: {has_coords}")
print(f"   有标签: {has_tags}")
print(f"   经纬度全为0: {beijing_attractions.count() - has_coords}")

if beijing_attractions.exists():
    sample = beijing_attractions.first()
    print(f"\n样本景点经纬度: ({sample.longitude}, {sample.latitude})")
    print(f"样本景点标签: '{sample.tags}'")