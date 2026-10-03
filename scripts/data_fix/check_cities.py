"""功能说明：检查数据库中的城市分布。"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

from travel.models import Attraction
from django.db.models import Count

print("=" * 60)
print("📍 数据库城市分布统计")
print("=" * 60)

city_stats = Attraction.objects.values('city_name').annotate(count=Count('id')).order_by('-count')

total = 0
for stat in city_stats:
    city = stat['city_name'] or '(未设置)'
    count = stat['count']
    total += count
    print(f"  {city}: {count} 个景点")

print(f"\n{'=' * 60}")
print(f"📊 总计: {total} 个景点")
print(f"{'=' * 60}")

# 检查是否有未导入的数据
print("\n💡 提示：如果总数远少于 226，说明 SQL 数据未完全导入")