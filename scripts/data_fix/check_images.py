"""功能说明：检查景点图片URL和整体数据状况。"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from travel.models import Attraction
from django.db.models import Count

print("=" * 70)
print("[CHECK] Attraction Data Status")
print("=" * 70)

total = Attraction.objects.count()
has_image = Attraction.objects.exclude(image__isnull=True).exclude(image__exact='').count()
no_image = total - has_image
has_coords = Attraction.objects.exclude(longitude=0.0).count()
has_tags = Attraction.objects.exclude(tags__isnull=True).exclude(tags__exact='').count()

print(f"\n  Total: {total}")
print(f"  Has image: {has_image}")
print(f"  No image:  {no_image}")
print(f"  Has coords: {has_coords}")
print(f"  Has tags:   {has_tags}")

print("\n--- Sample images (first 10) ---")
for attr in Attraction.objects.all()[:10]:
    print(f"  [{attr.city_name}] {attr.name}")
    print(f"    image: {attr.image}")
    print(f"    detail_url: {attr.detail_url}")

print("\n--- City distribution ---")
city_stats = Attraction.objects.values('city_name').annotate(count=Count('id')).order_by('-count')
for stat in city_stats:
    print(f"  {stat['city_name']}: {stat['count']}")

print("\n--- Attractions with NULL/empty image ---")
no_image_attrs = Attraction.objects.filter(image__isnull=True) | Attraction.objects.filter(image__exact='')
for attr in no_image_attrs[:10]:
    print(f"  [{attr.city_name}] {attr.name} - image: '{attr.image}'")