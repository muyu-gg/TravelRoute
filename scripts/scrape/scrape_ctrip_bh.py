import subprocess
import json
import sys
import os
import time
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CITIES = {
    'beijing1': '北京',
    'shanghai2': '上海',
    'guangzhou152': '广州',
    'shenzhen144': '深圳',
    'chengdu104': '成都',
    'hangzhou14': '杭州',
    'xian7': '西安',
    'suzhou9': '苏州',
    'nanjing12': '南京',
    'chongqing158': '重庆',
    'wuhan17': '武汉',
    'changsha148': '长沙',
    'zhengzhou4': '郑州',
    'kunming1': '昆明',
    'dali111': '大理',
    'lijiang31': '丽江',
    'xiamen53': '厦门',
    'qingdao3': '青岛',
    'dalian4': '大连',
    'haerbin151': '哈尔滨',
    'tianjin5': '天津',
    'sanya61': '三亚',
    'guilin3': '桂林',
    'huangshan18': '黄山',
    'luoyang98': '洛阳',
}

SKIP_PATTERNS = re.compile(
    r'^(酒店|机票|火车|旅游|门票|汽车|用车|攻略|搜索|位置|类型|排序|只看|可订|免费|滑雪|必打|亲子|赏秋|特色|夜游|携程|登录|注册|我的|联系|关于|首页|景点|住宿|美食|购物|游记|度假|当地|中国|跳至|确定|部分|推荐|更多|NEW|起|随时|退|提前|天预约|闭园|条|点评|·|全球|亚洲|国内|国际|跟团|自由|定制|邮轮|一日|租车|社区|地图|金融|企业|老友|礼品|全球购|App|扫码|查看|页|门票|可订明日)$'
)

CITY_NAMES = set(CITIES.values())

def run_bh(script_content, timeout=45):
    script_path = os.path.join(BASE_DIR, '_bh_scratch.py')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    env = os.environ.copy()
    env['BU_CDP_URL'] = 'http://localhost:9222'
    try:
        with open(script_path, 'r', encoding='utf-8') as stdin_file:
            result = subprocess.run(
                ['browser-harness'],
                stdin=stdin_file,
                capture_output=True,
                timeout=timeout,
                env=env,
                cwd=BASE_DIR,
                shell=True,
            )
        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        return stdout
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
            except OSError:
                pass

def scrape_city(city_code, city_name, max_pages=5):
    all_sights = []
    for page in range(max_pages):
        url = f"https://you.ctrip.com/sight/{city_code}/s0-p{page}.html"
        print(f"  Page {page+1}/{max_pages}: {url}")
        
        script = f'''new_tab("{url}")
wait_for_load(timeout=20)
result = js("JSON.stringify(document.body.innerText)")
print("PAGE_TEXT:", result)
'''
        output = run_bh(script, timeout=30)
        
        page_text = ''
        for line in output.split('\n'):
            stripped = line.strip()
            if stripped.startswith('PAGE_TEXT:'):
                json_str = stripped[10:].strip()
                try:
                    page_text = json.loads(json_str)
                except json.JSONDecodeError:
                    page_text = json_str
                break
        
        if not page_text:
            print(f"    No data from page {page+1}")
            time.sleep(2)
            continue
        
        sights = parse_page_text(page_text, city_name)
        if sights:
            all_sights.extend(sights)
            print(f"    Got {len(sights)} sights from page {page+1}")
        else:
            print(f"    No sights parsed from page {page+1}")
        
        time.sleep(3)
    
    return all_sights

def parse_page_text(text, city_name):
    sights = []
    lines = text.split('\n')
    lines = [l.strip() for l in lines if l.strip()]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        score_match = re.match(r'^(\d+\.\d+)/5$', line)
        if score_match:
            score = score_match.group(1)
            name = ''
            tags = []
            comments = ''
            price = ''
            is_free = False
            distance = ''
            area = ''
            
            j = i - 1
            while j >= 0 and j > i - 15:
                prev = lines[j]
                if re.match(r'^\d+\.\d+/5$', prev):
                    break
                if re.match(r'^[\uffe5\u00a5]\d+', prev) or prev == '免费':
                    break
                if re.match(r'^\d+$', prev) and len(prev) <= 5:
                    j -= 1
                    continue
                if not name and len(prev) > 1 and len(prev) < 50:
                    if not SKIP_PATTERNS.match(prev) and prev not in CITY_NAMES:
                        if not re.match(r'^\d+\.\d+$', prev):
                            name = prev
                j -= 1
            
            k = i + 1
            while k < len(lines) and k < i + 12:
                nxt = lines[k]
                if re.match(r'^\d+\.\d+/5$', nxt):
                    break
                if not comments and re.match(r'^[\d.]+万?条点评$', nxt):
                    comments = nxt
                if not price and re.match(r'^[\uffe5\u00a5](\d+)起?$', nxt):
                    price = re.sub(r'^[\uffe5\u00a5]', '', nxt).replace('起', '')
                if nxt == '免费':
                    is_free = True
                if not distance and re.match(r'^距市中心', nxt):
                    distance = nxt.replace('距市中心', '')
                if re.match(r'^(5A|4A|3A)$', nxt):
                    tags.append(nxt)
                if re.match(r'2026.*打卡|宝藏地|胜地|观景', nxt):
                    tags.append(nxt)
                if not area and re.match(r'.*地区$', nxt):
                    area = nxt
                k += 1
            
            if name and score:
                sights.append({
                    'name': name,
                    'score': score,
                    'comments': comments,
                    'price': price,
                    'isFree': is_free,
                    'distance': distance,
                    'area': area,
                    'tags': ','.join(tags),
                })
        
        i += 1
    
    seen = set()
    unique = []
    for s in sights:
        key = s['name']
        if key not in seen:
            seen.add(key)
            unique.append(s)
    
    return unique

def save_to_db(all_sights, city_name):
    venv_python = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
    data_json = json.dumps({'city_name': city_name, 'sights': all_sights}, ensure_ascii=False)
    
    save_script = '''
import json, sys, os, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
sys.path.insert(0, r"{base_dir}")
import django; django.setup()
from travel.models import Attraction

data = json.loads(r"""{data_raw}""")
city_name = data['city_name']
sights = data['sights']
saved = 0
for s in sights:
    name = s.get('name', '').strip()
    if not name or len(name) < 2: continue
    score_str = s.get('score', '')
    try: score = float(score_str) if score_str else 0
    except ValueError: score = 0
    price_str = s.get('price', '')
    is_free = s.get('isFree', False)
    comments_str = s.get('comments', '')
    try:
        if '万' in comments_str:
            comment_count = float(re.sub(r'[万条点评]', '', comments_str)) * 10000
        else:
            comment_count = float(re.sub(r'[条点评]', '', comments_str))
    except: comment_count = 0
    poi_id = abs(hash(name + city_name)) % (10**9)
    obj, created = Attraction.objects.update_or_create(
        poi_id=poi_id,
        defaults={{
            'name': name, 'city_name': city_name, 'score': score,
            'comment_count': comment_count,
            'actual_price': '免费' if is_free else ('¥{{}}'.format(price_str) if price_str else '暂无'),
            'is_free': is_free,
            'market_price': float(price_str) if price_str else None,
            'distance': s.get('distance', ''), 'area': s.get('area', ''),
            'tags': s.get('tags', ''), 'detail_url': 'https://you.ctrip.com/sight/',
            'is_advertisement': False, 'is_recommend': score >= 4.5,
            'longitude': 0, 'latitude': 0,
        }}
    )
    if created: saved += 1
print(f"SAVED:{{saved}}")
'''.format(base_dir=BASE_DIR, data_raw=data_json.replace('"""', ''))
    
    script_path = os.path.join(BASE_DIR, '_bh_save.py')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(save_script)
    
    try:
        result = subprocess.run(
            [venv_python, script_path],
            capture_output=True,
            timeout=30,
            cwd=BASE_DIR,
        )
        output = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        saved = 0
        for line in output.split('\n'):
            if line.strip().startswith('SAVED:'):
                saved = int(line.strip().split(':')[1])
                break
        print(f"  Saved {saved} new sights for {city_name}")
        return saved
    except Exception as e:
        print(f"  Save error: {e}")
        return 0
    finally:
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
            except OSError:
                pass

def export_sql():
    venv_python = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
    sql_path = os.path.join(BASE_DIR, 'attraction_data.sql')
    
    export_script = f'''
import sys, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
sys.path.insert(0, r"{BASE_DIR}")
import django; django.setup()
from travel.models import Attraction

attractions = Attraction.objects.all().order_by('city_name', '-score')
with open(r"{sql_path}", 'w', encoding='utf-8') as f:
    f.write("-- ============================================\\n")
    f.write("-- Ctrip attraction data (auto-generated)\\n")
    f.write(f"-- Total: {{attractions.count()}} sights\\n")
    f.write("-- ============================================\\n\\n")
    f.write("USE `travel_route_base`;\\n\\n")
    f.write("DELETE FROM `attraction`;\\n\\n")
    for a in attractions:
        def esc(v): return (v or '').replace("'", "\\\\'")
        f.write(
            f"INSERT INTO `attraction` (`poi_id`, `area`, `name`, `comment_count`, `score`, "
            f"`is_advertisement`, `is_recommend`, `city_name`, `image`, `distance`, `tags`, "
            f"`detail_url`, `market_price`, `preferential_price`, `preferential_desc`, "
            f"`actual_price`, `price_type`, `price_type_desc`, `is_free`, `longitude`, `latitude`, `heat_score`) VALUES "
            f"({{a.poi_id}}, '{{esc(a.area)}}', '{{esc(a.name)}}', {{a.comment_count or 0}}, {{a.score}}, "
            f"{{1 if a.is_advertisement else 0}}, {{1 if a.is_recommend else 0}}, '{{esc(a.city_name)}}', "
            f"NULL, '{{esc(a.distance)}}', '{{esc(a.tags)}}', "
            f"'{{esc(a.detail_url)}}', "
            f"{{'NULL' if a.market_price is None else a.market_price}}, "
            f"{{'NULL' if a.preferential_price is None else a.preferential_price}}, "
            f"NULL, "
            f"'{{esc(a.actual_price)}}', "
            f"NULL, NULL, "
            f"{{1 if a.is_free else 0}}, {{a.longitude}}, {{a.latitude}}, "
            f"NULL);\\n"
        )
print(f"EXPORTED:{{attractions.count()}}")
'''
    
    script_path = os.path.join(BASE_DIR, '_bh_export.py')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(export_script)
    
    try:
        result = subprocess.run(
            [venv_python, script_path],
            capture_output=True,
            timeout=60,
            cwd=BASE_DIR,
        )
        output = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        count = 0
        for line in output.split('\n'):
            if line.strip().startswith('EXPORTED:'):
                count = int(line.strip().split(':')[1])
                break
        print(f"\n  SQL exported to: {sql_path}")
        print(f"  Total: {count} sights")
    except Exception as e:
        print(f"  Export error: {e}")
    finally:
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
            except OSError:
                pass

def main():
    print("=" * 60)
    print("  Ctrip Sight Scraper (browser-harness)")
    print("  Chrome must be running with --remote-debugging-port=9222")
    print("=" * 60)
    
    total_saved = 0
    for city_code, city_name in CITIES.items():
        print(f"\n[{city_name}] Scraping...")
        sights = scrape_city(city_code, city_name, max_pages=5)
        print(f"  Total extracted: {len(sights)} sights")
        
        if sights:
            saved = save_to_db(sights, city_name)
            total_saved += saved
        
        time.sleep(5)
    
    print(f"\n{'=' * 60}")
    print(f"  Scraping done! Total saved: {total_saved} sights")
    print(f"{'=' * 60}")
    
    print("\nExporting to SQL...")
    export_sql()

if __name__ == '__main__':
    main()