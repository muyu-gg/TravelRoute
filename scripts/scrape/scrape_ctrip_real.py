"""功能说明：使用 browser-harness 从携程爬取真实景点数据并入库。

使用方法：
  1. 先启动 Chrome 调试模式：
     关闭所有 Chrome，然后运行：
     "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --no-first-run --user-data-dir="%TEMP%\chrome-cdp-profile"
  2. 运行本脚本：
     python scrape_ctrip_real.py
     python scrape_ctrip_real.py --city 北京
     python scrape_ctrip_real.py --pages 3
"""
import json
import os
import re
import subprocess
import sys
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from travel.models import Attraction

CTRIP_CITIES = {
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

EXTRACT_JS = """
(function() {
    var cards = document.querySelectorAll('[class*="sightItemCard"]');
    var results = [];
    for (var i = 0; i < cards.length; i++) {
        var card = cards[i];
        var nameEl = card.querySelector('[class*="titleModule_name"] a');
        var name = nameEl ? nameEl.textContent.trim() : '';
        var link = nameEl ? nameEl.href : '';
        var poiId = '';
        if (link) {
            var m = link.match(/sight\\/[a-z]+\\d+\\/(\\d+)/);
            if (m) poiId = m[1];
        }
        var cardText = card.innerText;
        var score = '';
        var sm = cardText.match(/(\\d+\\.\\d+)\\/5/);
        if (sm) score = sm[1];
        var comments = '';
        var cm = cardText.match(/([\\d.]+\\u4e07?\\u6761\\u70b9\\u8bc4)/);
        if (cm) comments = cm[1];
        var price = '';
        var pm = cardText.match(/\\u00a5(\\d+)/);
        if (pm) price = pm[1];
        var isFree = cardText.indexOf('\\u514d\\u8d39') > -1;
        var distance = '';
        var dm = cardText.match(/\\u8ddd\\u5e02\\u4e2d\\u5fc3([\\d.km]+)/);
        if (dm) distance = dm[1];
        var level = '';
        var lm = cardText.match(/(5A|4A|3A)/);
        if (lm) level = lm[1];
        var image = '';
        var imgEl = card.querySelector('img[class*="coverModule"]');
        if (imgEl && imgEl.src) image = imgEl.src;
        var area = '';
        var am = cardText.match(/([\\u4e00-\\u9fff]+[\\u5730\\u533a])/);
        if (am) area = am[1];
        if (name && poiId) {
            results.push({
                name: name, poiId: poiId, score: score, comments: comments,
                price: price, isFree: isFree, distance: distance, level: level,
                link: link, image: image, area: area
            });
        }
    }
    return JSON.stringify(results);
})()
"""


def run_bh_script(script_content, timeout=60):
    """功能说明：执行 browser-harness 脚本。"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_bh_tmp_script.py')
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        env = os.environ.copy()
        env['PYTHONPATH'] = r'C:\Users\29346\AppData\Roaming\Python\Python314\site-packages'
        result = subprocess.run(
            f'python -m browser_harness.run < "{script_path}"',
            capture_output=True,
            timeout=timeout,
            shell=True,
            env=env,
        )
        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
        if stderr:
            print(f'    BH stderr: {stderr[-500:]}')
        if not stdout or 'RESULT' not in stdout:
            print(f'    BH stdout (no RESULT): {stdout[:500]}')
        return stdout
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'
    except Exception as e:
        return f'ERROR: {e}'
    finally:
        pass


def scrape_city(city_name, city_slug, max_pages=5):
    """功能说明：爬取指定城市的景点数据。"""
    all_sights = []

    for page in range(1, max_pages + 1):
        url = f'https://you.ctrip.com/sight/{city_slug}/s0-p{page}.html'
        print(f'  第 {page}/{max_pages} 页: {url}')

        script = f'new_tab("{url}")\nwait_for_load(timeout=20)\nimport time\ntime.sleep(8)\n'
        script += f'data = js("""{EXTRACT_JS}""")\nprint("RESULT:", data)\n'

        output = run_bh_script(script, timeout=60)

        sights = []
        for line in output.split('\n'):
            stripped = line.strip()
            if stripped.startswith('RESULT:'):
                json_str = stripped[7:].strip()
                try:
                    sights = json.loads(json_str)
                except json.JSONDecodeError:
                    print(f'    JSON 解析失败: {json_str[:100]}')
                break

        if sights:
            all_sights.extend(sights)
            print(f'    ✅ 获取 {len(sights)} 个景点')
        else:
            print(f'    — 第 {page} 页无数据，停止翻页')
            break

        time.sleep(3)

    seen = {}
    unique = []
    for s in all_sights:
        key = s.get('poiId', '')
        if key and key not in seen:
            seen[key] = True
            unique.append(s)

    return unique


def ctrip_image_hd(url, width=800, height=600):
    """功能说明：将携程 CDN 缩略图 URL 转为高清尺寸。"""
    if not url:
        return url
    return re.sub(r'_[CRW]_(\d+)_(\d+)(\.\w+)', f'_R_{width}_{height}\\3', url)


def save_to_db(sights, city_name, city_slug):
    """功能说明：将景点数据保存到数据库。"""
    saved = 0
    updated = 0

    for s in sights:
        poi_id = int(s.get('poiId', 0))
        if not poi_id:
            continue

        name = s.get('name', '').strip()
        if not name or len(name) < 2:
            continue

        score = float(s.get('score', 0) or 0)
        comments_str = s.get('comments', '')
        comment_count = 0
        if comments_str:
            try:
                if '万' in comments_str:
                    comment_count = float(re.sub(r'[万条点评]', '', comments_str)) * 10000
                else:
                    comment_count = float(re.sub(r'[条点评]', '', comments_str))
            except ValueError:
                comment_count = 0

        price_str = s.get('price', '')
        is_free = s.get('isFree', False)
        market_price = float(price_str) if price_str else None
        actual_price = '免费' if is_free else (f'¥{price_str}' if price_str else '暂无报价')

        distance_str = s.get('distance', '')
        distance_center = 0
        if distance_str:
            dm = re.match(r'([\d.]+)', distance_str)
            if dm:
                distance_center = float(dm.group(1))

        detail_url = f'https://you.ctrip.com/sight/{city_slug}/s{poi_id}.html'
        level = s.get('level', '')
        tags = level if level else ''

        obj, created = Attraction.objects.update_or_create(
            poi_id=poi_id,
            defaults={
                'name': name,
                'city_name': city_name,
                'score': score,
                'comment_count': comment_count,
                'actual_price': actual_price,
                'is_free': is_free,
                'market_price': market_price,
                'preferential_price': market_price,
                'distance': distance_str,
                'distance_center': distance_center,
                'detail_url': detail_url,
                'tags': tags,
                'area': s.get('area', ''),
                'image': ctrip_image_hd(s.get('image', ''), 800, 600),
                'banner_url': ctrip_image_hd(s.get('image', ''), 1200, 800),
                'is_advertisement': False,
                'is_recommend': score >= 4.5,
                'longitude': 0,
                'latitude': 0,
            },
        )
        if created:
            saved += 1
        else:
            updated += 1

    return saved, updated


def main():
    import argparse
    parser = argparse.ArgumentParser(description='携程景点数据爬取')
    parser.add_argument('--city', type=str, default='', help='只爬取指定城市')
    parser.add_argument('--pages', type=int, default=5, help='每个城市爬取页数')
    args = parser.parse_args()

    cities = CTRIP_CITIES
    if args.city:
        if args.city in cities:
            cities = {args.city: cities[args.city]}
        else:
            print(f'城市 "{args.city}" 未配置，支持: {", ".join(CTRIP_CITIES.keys())}')
            return

    total_saved = 0
    total_updated = 0

    for city_name, city_slug in cities.items():
        print(f'\n{"=" * 50}')
        print(f'爬取 {city_name} ({city_slug})')
        print(f'{"=" * 50}')

        sights = scrape_city(city_name, city_slug, args.pages)
        print(f'  共获取 {len(sights)} 个不重复景点')

        if sights:
            saved, updated = save_to_db(sights, city_name, city_slug)
            total_saved += saved
            total_updated += updated
            print(f'  ✅ 新增 {saved} 条，更新 {updated} 条')
        else:
            print(f'  ❌ 无数据')

    print(f'\n{"=" * 50}')
    print(f'全部完成: 新增 {total_saved} 条，更新 {total_updated} 条')
    print(f'数据库总景点数: {Attraction.objects.count()}')


if __name__ == '__main__':
    main()