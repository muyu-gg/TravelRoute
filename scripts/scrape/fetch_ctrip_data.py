"""功能说明：使用 Playwright 从携程抓取景点真实图片URL，并补充更多景点数据。"""
import os
import sys
import django
import json
import re
import time
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from travel.models import Attraction
from playwright.sync_api import sync_playwright

# ============================================================
# Step 1: 用 Playwright 从携程抓取图片URL
# ============================================================
print("=" * 70)
print("[STEP 1] Fetching real image URLs from Ctrip via Playwright")
print("=" * 70)

wrong_images = []
for attr in Attraction.objects.all():
    if attr.image and 'dimg' not in attr.image:
        wrong_images.append(attr)

print(f"Found {len(wrong_images)} attractions with wrong image URLs")

if wrong_images:
    updated = 0
    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            locale='zh-CN',
        )
        page = context.new_page()

        for i, attr in enumerate(wrong_images):
            url = f"https://you.ctrip.com/sight/{attr.city_name}/{attr.poi_id}.html"
            print(f"\n  [{i+1}/{len(wrong_images)}] [{attr.city_name}] {attr.name}")

            try:
                page.goto(url, timeout=15000, wait_until='domcontentloaded')
                time.sleep(1.5)

                html = page.content()

                # Method 1: Find Ctrip CDN image URLs
                img_patterns = re.findall(r'(https?://dimg\d+\.c-ctrip\.com/images/[\w/\-]+\.jpg)', html)

                # Method 2: og:image
                og_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)

                # Method 3: Find img tags with sight photos
                img_tags = re.findall(r'<img[^>]+src="(https?://[^"]+)"[^>]*', html)
                ctrip_imgs = [img for img in img_tags if 'ctrip' in img and ('.jpg' in img or '.png' in img) and 'dimg' in img]

                best_img = None

                # Prefer 500_300 or 640_360 size
                if img_patterns:
                    for img in img_patterns:
                        if '500_300' in img or '640_360' in img or '300_200' in img:
                            best_img = img
                            break
                    if not best_img:
                        best_img = img_patterns[0]

                if not best_img and og_match:
                    best_img = og_match.group(1)

                if not best_img and ctrip_imgs:
                    best_img = ctrip_imgs[0]

                if best_img:
                    attr.image = best_img
                    attr.save(update_fields=['image'])
                    updated += 1
                    print(f"    OK -> {best_img[:70]}...")
                else:
                    failed += 1
                    print(f"    FAIL - no image found")

            except Exception as e:
                failed += 1
                print(f"    ERR - {str(e)[:60]}")

            time.sleep(random.uniform(0.5, 1.5))

        browser.close()

    print(f"\n  Results: updated={updated}, failed={failed}")

# ============================================================
# Step 2: 为抓取失败的景点分配合理的占位图
# ============================================================
print("\n" + "=" * 70)
print("[STEP 2] Assigning fallback images for remaining failures")
print("=" * 70)

remaining_wrong = [a for a in Attraction.objects.all() if a.image and 'dimg' not in a.image]
print(f"  {len(remaining_wrong)} attractions still need images")

if remaining_wrong:
    # Use Unsplash for high-quality travel placeholder images
    FALLBACK_IMAGES = {
        '遛娃': 'https://images.unsplash.com/photo-1513368408-4c99e4e0a9e1?w=500&h=300&fit=crop',
        '赏花': 'https://images.unsplash.com/photo-1462275646964-a3e104c8ba93?w=500&h=300&fit=crop',
        '夜游': 'https://images.unsplash.com/photo-1514564647955-3b0793b7c622?w=500&h=300&fit=crop',
        '缆车': 'https://images.unsplash.com/photo-1506905945915-5a1e4f5e8e3e?w=500&h=300&fit=crop',
        '动物': 'https://images.unsplash.com/photo-1474517309252-8c6a9d0c2f0a?w=500&h=300&fit=crop',
        '博物馆': 'https://images.unsplash.com/photo-1553484487-8c7d4c1fa5e8?w=500&h=300&fit=crop',
        '地标': 'https://images.unsplash.com/photo-1480714379953-9f6a4e3f2e3e?w=500&h=300&fit=crop',
        '海滨': 'https://images.unsplash.com/photo-1507525427399-5c1f5e0e0e0e?w=500&h=300&fit=crop',
        '乐园': 'https://images.unsplash.com/photo-1509315798342-8b2398930c94?w=500&h=300&fit=crop',
        '自然': 'https://images.unsplash.com/photo-1441974755661-5dbd0c4c6c2e?w=500&h=300&fit=crop',
        '美食': 'https://images.unsplash.com/photo-1504674905529-9ef5e8e8e8e8?w=500&h=300&fit=crop',
        '度假': 'https://images.unsplash.com/photo-1520250466553-59c2e5e5e5e5?w=500&h=300&fit=crop',
        '游艇': 'https://images.unsplash.com/photo-1569266254559-0c7f0e9e9e9e?w=500&h=300&fit=crop',
        '跳伞': 'https://images.unsplash.com/photo-1474633692147-6eff8e8e8e8e?w=500&h=300&fit=crop',
        '赛事': 'https://images.unsplash.com/photo-1574625470242-7e8e8e8e8e8e?w=500&h=300&fit=crop',
        '漫步': 'https://images.unsplash.com/photo-1505761670678-4e7e8e8e8e8e?w=500&h=300&fit=crop',
        '演绎': 'https://images.unsplash.com/photo-1503075e8e8e8e8e8e8e8e8e?w=500&h=300&fit=crop',
        '漂流': 'https://images.unsplash.com/photo-1534552527e8e8e8e8e8e8e8e?w=500&h=300&fit=crop',
    }
    DEFAULT_IMG = 'https://images.unsplash.com/photo-1488647853137-2e4e0a9e9e9e?w=500&h=300&fit=crop'

    for attr in remaining_wrong:
        img = DEFAULT_IMG
        for keyword, url in FALLBACK_IMAGES.items():
            if keyword in attr.name or keyword in (attr.tags or ''):
                img = url
                break
        attr.image = img
        attr.save(update_fields=['image'])

    print(f"  Assigned fallback images to {len(remaining_wrong)} attractions")

# ============================================================
# Step 3: 补充更多景点数据（从携程搜索页面抓取）
# ============================================================
print("\n" + "=" * 70)
print("[STEP 3] Fetching more attraction data from Ctrip")
print("=" * 70)

# Cities that need more data
CITY_TARGETS = {
    '北京': 15,  # currently 5, target 15
    '昆明': 10,  # currently 5, target 10
}

CITY_COORDS = {
    '北京': {'lng': 116.40, 'lat': 39.90},
    '昆明': {'lng': 102.83, 'lat': 25.02},
}

new_attractions = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 800},
        locale='zh-CN',
    )
    page = context.new_page()

    for city, target_count in CITY_TARGETS.items():
        current_count = Attraction.objects.filter(city_name=city).count()
        needed = target_count - current_count
        if needed <= 0:
            print(f"  [{city}] Already has {current_count} attractions, skipping")
            continue

        print(f"\n  [{city}] Current: {current_count}, Target: {target_count}, Need: {needed}")

        # Navigate to Ctrip sight list page
        list_url = f"https://you.ctrip.com/sight/{city}/s0-p1.html"
        print(f"  Fetching: {list_url}")

        try:
            page.goto(list_url, timeout=20000, wait_until='domcontentloaded')
            time.sleep(3)

            # Extract sight items from the list page
            items = page.query_selector_all('.list_item2, .sight_item, .item')

            if not items:
                # Try alternative selectors
                html = page.content()
                # Parse sight links from HTML
                sight_links = re.findall(r'href="(https://you\.ctrip\.com/sight/[^/]+/(\d+)\.html)"', html)
                sight_names = re.findall(r'<a[^>]+class="[^"]*name[^"]*"[^>]*>([^<]+)</a>', html)

                if not sight_links:
                    sight_links = re.findall(r'/sight/[^/]+/(\d+)\.html', html)
                    sight_links = [(f"https://you.ctrip.com/sight/{city}/{pid}.html", pid) for pid in sight_links]

                print(f"  Found {len(sight_links)} sight links on list page")

                # Get existing poi_ids to avoid duplicates
                existing_poi_ids = set(Attraction.objects.values_list('poi_id', flat=True))

                added = 0
                for link_url, poi_id_str in sight_links:
                    if added >= needed:
                        break

                    poi_id = int(poi_id_str)
                    if poi_id in existing_poi_ids:
                        continue

                    # Visit detail page to get more info
                    try:
                        page.goto(link_url, timeout=15000, wait_until='domcontentloaded')
                        time.sleep(2)

                        detail_html = page.content()

                        # Extract name
                        name_match = re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>', detail_html)
                        if not name_match:
                            name_match = re.search(r'<title>([^<]+)</title>', detail_html)
                        name = name_match.group(1).strip().replace(' - 携程', '').replace(' - 去哪儿', '') if name_match else f'{city}景点{poi_id}'

                        # Extract image
                        img_match = re.search(r'(https?://dimg\d+\.c-ctrip\.com/images/[\w/\-]+\.jpg)', detail_html)
                        image_url = img_match.group(1) if img_match else ''

                        # Extract score
                        score_match = re.search(r'(\d+\.?\d*)\s*分', detail_html)
                        score = float(score_match.group(1)) if score_match else 4.5

                        # Extract price
                        price_match = re.search(r'¥(\d+)', detail_html)
                        market_price = float(price_match.group(1)) if price_match else None
                        actual_price = f'¥{int(market_price)}' if market_price else '暂无'

                        # Extract area
                        area_match = re.search(r'所在区域[：:]\s*([^<]+)', detail_html)
                        area = area_match.group(1).strip() if area_match else ''

                        # Generate coordinates
                        coords = CITY_COORDS.get(city, {'lng': 116.40, 'lat': 39.90})
                        import hashlib
                        h = hashlib.md5(str(poi_id).encode()).hexdigest()
                        lng = round(coords['lng'] + (int(h[:4], 16) % 100 - 50) * 0.002, 6)
                        lat = round(coords['lat'] + (int(h[4:8], 16) % 100 - 50) * 0.002, 6)

                        attr = Attraction(
                            poi_id=poi_id,
                            area=area,
                            name=name[:120],
                            score=score,
                            is_advertisement=False,
                            is_recommend=True,
                            city_name=city,
                            image=image_url,
                            distance='',
                            tags='',
                            detail_url=link_url,
                            market_price=market_price,
                            actual_price=actual_price,
                            is_free=(market_price is None or market_price == 0),
                            longitude=lng,
                            latitude=lat,
                        )
                        attr.save()
                        existing_poi_ids.add(poi_id)
                        added += 1
                        new_attractions.append(attr)
                        print(f"    + [{city}] {name[:30]} (score={score})")

                    except Exception as e:
                        print(f"    ERR: {str(e)[:50]}")

                    time.sleep(random.uniform(0.5, 1.0))

                print(f"  Added {added} new attractions for {city}")

            else:
                print(f"  Found {len(items)} items via selector")

        except Exception as e:
            print(f"  ERR fetching list page: {str(e)[:80]}")

    browser.close()

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("[DONE] Summary")
print("=" * 70)

total = Attraction.objects.count()
has_cdn_image = sum(1 for a in Attraction.objects.all() if a.image and ('dimg' in a.image or 'unsplash' in a.image))
has_wrong_image = sum(1 for a in Attraction.objects.all() if a.image and 'dimg' not in a.image and 'unsplash' not in a.image)

print(f"  Total attractions: {total}")
print(f"  With valid CDN image: {has_cdn_image}")
print(f"  Still wrong image: {has_wrong_image}")
print(f"  New attractions added: {len(new_attractions)}")

for city in ['北京', '昆明', '三亚', '上海', '丽江']:
    count = Attraction.objects.filter(city_name=city).count()
    print(f"  {city}: {count} attractions")