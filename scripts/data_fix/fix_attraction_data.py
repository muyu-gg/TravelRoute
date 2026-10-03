"""功能说明：修复 attraction 表中的 detail_url，并补充缺失数据。

第一步：修复 detail_url 格式
  当前错误格式：https://you.ctrip.com/sight/上海/454516364.html
  正确格式：    https://you.ctrip.com/sight/shanghai2/s454516364.html

第二步：使用高德地图 API 补充经纬度（如果经纬度为 0）

使用方法：
  python fix_attraction_data.py              # 修复 detail_url + 补充经纬度
  python fix_attraction_data.py --detail     # 额外爬取详情页补充 banner_url 等
"""
import os
import sys
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from travel.models import Attraction

CTRIP_CITY_SLUG = {
    '北京': 'beijing1',
    '上海': 'shanghai2',
    '广州': 'guangzhou152',
    '深圳': 'shenzhen144',
    '成都': 'chengdu104',
    '杭州': 'hangzhou14',
    '西安': 'xian7',
    '苏州': 'suzhou9',
    '南京': 'nanjing12',
    '重庆': 'chongqing158',
    '武汉': 'wuhan17',
    '长沙': 'changsha148',
    '郑州': 'zhengzhou4',
    '昆明': 'kunming1',
    '大理': 'dali111',
    '丽江': 'lijiang31',
    '厦门': 'xiamen53',
    '青岛': 'qingdao3',
    '大连': 'dalian4',
    '哈尔滨': 'haerbin151',
    '天津': 'tianjin5',
    '三亚': 'sanya61',
    '桂林': 'guilin3',
    '黄山': 'huangshan18',
    '洛阳': 'luoyang98',
}


def fix_detail_urls():
    """功能说明：修复所有 detail_url 为正确的携程格式。"""
    total = Attraction.objects.count()
    fixed = 0

    for attr in Attraction.objects.iterator(chunk_size=100):
        slug = CTRIP_CITY_SLUG.get(attr.city_name)
        if not slug:
            print(f'  ⚠️ 城市未配置: {attr.city_name} (poi={attr.poi_id})')
            continue

        correct_url = f'https://you.ctrip.com/sight/{slug}/s{attr.poi_id}.html'

        if attr.detail_url != correct_url:
            attr.detail_url = correct_url
            attr.save(update_fields=['detail_url'])
            fixed += 1

    print(f'✅ detail_url 修复完成: {fixed}/{total} 条已更正')


def fix_coordinates():
    """功能说明：使用高德地图 API 为经纬度为 0 的景点补充坐标。"""
    from planner.amap_service import geocode

    zero_coords = Attraction.objects.filter(longitude=0, latitude=0)
    total = zero_coords.count()
    if total == 0:
        print('✅ 所有景点已有坐标，无需补充')
        return

    print(f'📍 开始为 {total} 个景点补充坐标...')
    fixed = 0

    for attr in zero_coords.iterator(chunk_size=50):
        location = geocode(attr.name, attr.city_name)
        if location and ',' in location:
            lng, lat = location.split(',')
            attr.longitude = float(lng)
            attr.latitude = float(lat)
            attr.save(update_fields=['longitude', 'latitude'])
            fixed += 1
            print(f'  ✅ {attr.name} → {location}')
        else:
            print(f'  ❌ {attr.name} ({attr.city_name}) 坐标解析失败')

        time.sleep(0.3)

    print(f'✅ 坐标补充完成: {fixed}/{total}')


def scrape_details_with_bh():
    """功能说明：使用 browser-harness 爬取景点详情页，补充 banner_url、activity_name 等。"""
    import subprocess
    import json
    import re

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    need_detail = Attraction.objects.filter(banner_url='').exclude(detail_url='')
    total = need_detail.count()
    if total == 0:
        print('✅ 所有景点已有详情数据')
        return

    print(f'🌐 开始爬取 {total} 个景点详情页...')

    for idx, attr in enumerate(need_detail.iterator(chunk_size=50), 1):
        url = attr.detail_url
        print(f'  [{idx}/{total}] {attr.name} → {url}')

        script = f'''new_tab("{url}")
wait_for_load(timeout=15)
result = js("JSON.stringify({{banner: (document.querySelector('.detailTopImg img') || document.querySelector('.banner-img img') || {{}}).src || '', activity: (document.querySelector('.activity-name') || {{}}).textContent || '', activityTime: (document.querySelector('.activity-time') || {{}}).textContent || '', intro: (document.querySelector('.module-info .des') || document.querySelector('.intro') || {{}}).textContent || '', imgList: Array.from(document.querySelectorAll('.detailTopImg img, .banner-img img, .sight-detail img')).slice(0, 3).map(i => i.src).filter(Boolean)}})")
print("DETAIL:", result)
'''
        try:
            result = subprocess.run(
                ['browser-harness'],
                input=script.encode('utf-8'),
                capture_output=True,
                timeout=30,
                cwd=BASE_DIR,
                shell=True,
            )
            output = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        except Exception as e:
            print(f'    ❌ 爬取失败: {e}')
            time.sleep(2)
            continue

        detail_data = {}
        for line in output.split('\n'):
            stripped = line.strip()
            if stripped.startswith('DETAIL:'):
                try:
                    detail_data = json.loads(stripped[7:].strip())
                except json.JSONDecodeError:
                    pass
                break

        if detail_data:
            updated = False
            banner = detail_data.get('banner', '')
            if banner and not attr.banner_url:
                attr.banner_url = banner
                updated = True

            activity = detail_data.get('activity', '').strip()
            if activity and not attr.activity_name:
                attr.activity_name = activity[:100]
                updated = True

            activity_time = detail_data.get('activityTime', '').strip()
            if activity_time and not attr.activity_time:
                attr.activity_time = activity_time[:100]
                updated = True

            img_list = detail_data.get('imgList', [])
            if img_list and not attr.banner_url:
                attr.banner_url = img_list[0]
                updated = True

            if updated:
                attr.save(update_fields=['banner_url', 'activity_name', 'activity_time'])
                print(f'    ✅ 已补充详情数据')
            else:
                print(f'    — 无新数据')
        else:
            print(f'    — 详情页解析为空')

        time.sleep(2)

    print(f'✅ 详情爬取完成')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='修复景点数据')
    parser.add_argument('--detail', action='store_true', help='爬取详情页补充 banner_url 等')
    args = parser.parse_args()

    print('=' * 50)
    print('第一步：修复 detail_url')
    print('=' * 50)
    fix_detail_urls()

    print()
    print('=' * 50)
    print('第二步：补充经纬度坐标')
    print('=' * 50)
    fix_coordinates()

    if args.detail:
        print()
        print('=' * 50)
        print('第三步：爬取详情页补充数据')
        print('=' * 50)
        scrape_details_with_bh()


if __name__ == '__main__':
    main()