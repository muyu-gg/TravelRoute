"""功能说明：使用 browser-harness 从携程抓取景点图片URL。"""
import subprocess
import sys
import os
import json
import time
import re

BASE_DIR = r"D:\BaiduNetdiskDownload\S028 基于Python+LangGraph的旅游规划系统与实现\赠送资料\travel_route\travel_route"

def run_bh(script):
    result = subprocess.run(
        ["browser-harness"],
        input=script,
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        timeout=60,
    )
    return result.stdout + result.stderr

# Step 1: Get list of attractions with wrong images from Django
print("Step 1: Getting attractions with wrong images...")
get_data_script = """
import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()
from travel.models import Attraction
wrong = []
for attr in Attraction.objects.all():
    if attr.image and 'dimg' not in attr.image:
        wrong.append({'id': attr.id, 'name': attr.name, 'city': attr.city_name, 'poi_id': attr.poi_id})
print(json.dumps(wrong[:5]))  # First 5 for testing
"""

# Actually, let's just use Django directly and then use browser-harness for each URL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
import django
django.setup()

from travel.models import Attraction

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

wrong_images = []
for attr in Attraction.objects.all():
    if attr.image and 'dimg' not in attr.image:
        wrong_images.append(attr)

print(f"Found {len(wrong_images)} attractions with wrong image URLs")

# Test with first 5
test_attrs = wrong_images[:5]
updated = 0

for attr in test_attrs:
    url = f"https://you.ctrip.com/sight/{attr.city_name}/{attr.poi_id}.html"
    print(f"\nFetching: [{attr.city_name}] {attr.name}")
    print(f"  URL: {url}")

    # Use browser-harness to navigate and extract image
    bh_script = f"""
import time, json, re
try:
    new_tab("{url}")
    time.sleep(3)
    html = js("document.documentElement.outerHTML")
    # Find Ctrip CDN image URLs
    imgs = re.findall(r'(https?://dimg\\d+\\.c-ctrip\\.com/images/[\\w/]+\\.jpg)', html)
    # Also try og:image
    og = re.search(r'<meta\\s+property="og:image"\\s+content="([^"]+)"', html)
    result = {{"imgs": imgs[:5], "og": og.group(1) if og else None}}
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""

    try:
        result = subprocess.run(
            ["browser-harness"],
            input=bh_script,
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=30,
        )
        output = result.stdout.strip()
        print(f"  Result: {output[:200]}")

        # Parse the JSON result
        try:
            data = json.loads(output.split('\n')[-1])
            if data.get('imgs'):
                best_img = None
                for img in data['imgs']:
                    if '500_300' in img or '300_200' in img or '640_360' in img:
                        best_img = img
                        break
                if not best_img:
                    best_img = data['imgs'][0]

                attr.image = best_img
                attr.save(update_fields=['image'])
                updated += 1
                print(f"  -> Updated: {best_img[:60]}...")
            elif data.get('og'):
                attr.image = data['og']
                attr.save(update_fields=['image'])
                updated += 1
                print(f"  -> Updated (og): {data['og'][:60]}...")
            else:
                print(f"  -> No image found")
        except json.JSONDecodeError:
            print(f"  -> Could not parse result")

    except subprocess.TimeoutExpired:
        print(f"  -> Timeout")
    except Exception as e:
        print(f"  -> Error: {e}")

    time.sleep(1)

print(f"\nUpdated {updated}/{len(test_attrs)} test attractions")