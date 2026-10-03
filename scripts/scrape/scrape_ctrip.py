"""功能说明：携程景点数据爬取脚本。

使用方法：
    python scrape_ctrip.py --city 成都 --pages 5

环境要求：
    pip install requests
"""
import argparse
import json
import math
import re
import time
from pathlib import Path

import requests


CTRIP_ATTRACTION_URL = 'https://you.ctrip.com/sight/{city_pinyin}/{city_id}/s0-p{page}.html'


CITY_CONFIG = {
    '成都': {'city_pinyin': 'chengdu', 'city_id': 104},
    '北京': {'city_pinyin': 'beijing', 'city_id': 1},
    '上海': {'city_pinyin': 'shanghai', 'city_id': 2},
    '杭州': {'city_pinyin': 'hangzhou', 'city_id': 14},
    '广州': {'city_pinyin': 'guangzhou', 'city_id': 32},
    '重庆': {'city_pinyin': 'chongqing', 'city_id': 158},
    '西安': {'city_pinyin': 'xian', 'city_id': 10},
    '南京': {'city_pinyin': 'nanjing', 'city_id': 18},
    '苏州': {'city_pinyin': 'suzhou', 'city_id': 17},
    '武汉': {'city_pinyin': 'wuhan', 'city_id': 477},
    '长沙': {'city_pinyin': 'changsha', 'city_id': 327},
    '厦门': {'city_pinyin': 'xiamen', 'city_id': 36},
    '昆明': {'city_pinyin': 'kunming', 'city_id': 29},
    '大理': {'city_pinyin': 'dali', 'city_id': 31},
    '丽江': {'city_pinyin': 'lijiang', 'city_id': 33},
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://you.ctrip.com/',
}


def fetch_attraction_page(city_pinyin: str, city_id: int, page: int) -> str:
    """功能说明：请求携程景点列表页面 HTML。"""
    url = CTRIP_ATTRACTION_URL.format(city_pinyin=city_pinyin, city_id=city_id, page=page)
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        print(f'  请求第 {page} 页失败：{exc}')
        return ''


def parse_attraction_list(html: str) -> list[dict]:
    """功能说明：从 HTML 中解析景点列表数据。"""
    attractions = []
    pattern = re.compile(
        r'<div\s+class="list_mod2"[^>]*>.*?'
        r'data-poiid="(\d+)".*?'
        r'class="title"[^>]*>(.*?)</a>.*?'
        r'class="score"[^>]*>([\d.]+)</strong>.*?'
        r'class="comment_count"[^>]*>(.*?)</a>.*?'
        r'</div>',
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        poi_id = int(match.group(1))
        name = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        score = float(match.group(3)) if match.group(3) else 0.0
        comment_text = re.sub(r'<[^>]+>', '', match.group(4)).strip()
        comment_count = float(re.sub(r'[^\d.]', '', comment_text)) if comment_text else 0

        attractions.append({
            'poi_id': poi_id,
            'name': name,
            'score': score,
            'comment_count': comment_count,
        })
    return attractions


def parse_attraction_detail_json(html: str) -> dict:
    """功能说明：从 HTML 中提取景点详情 JSON 数据。"""
    json_pattern = re.compile(r'window\.IM\+Context\s*=\s*({.*?});', re.DOTALL)
    match = json_pattern.search(html)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def clean_attraction_data(raw: dict, city_name: str) -> dict:
    """功能说明：清洗单条景点数据，返回可入库的字典。"""
    actual_price = str(raw.get('actualPrice') or raw.get('marketPrice') or '暂无报价')
    is_free = '免费' in actual_price or float(raw.get('marketPrice') or 999) == 0

    return {
        'poi_id': int(raw.get('poiId', 0)),
        'area': str(raw.get('districtName') or raw.get('areaName') or ''),
        'name': str(raw.get('name') or ''),
        'comment_count': float(raw.get('commentCount') or 0),
        'score': float(raw.get('score') or 0),
        'is_advertisement': bool(raw.get('isAd') or False),
        'is_recommend': bool(raw.get('isRecommend') or False),
        'city_name': city_name,
        'image': str(raw.get('image') or raw.get('coverImg') or ''),
        'distance': str(raw.get('distance') or ''),
        'tags': str(raw.get('tagList') or ''),
        'detail_url': str(raw.get('url') or ''),
        'market_price': float(raw.get('marketPrice') or 0) or None,
        'preferential_price': float(raw.get('preferentialPrice') or 0) or None,
        'preferential_desc': str(raw.get('preferentialDesc') or ''),
        'actual_price': actual_price,
        'price_type': int(raw.get('priceType') or 0) or None,
        'price_type_desc': str(raw.get('priceTypeDesc') or ''),
        'is_free': is_free,
        'longitude': float(raw.get('longitude') or raw.get('lng') or 0),
        'latitude': float(raw.get('latitude') or raw.get('lat') or 0),
        'heat_score': float(raw.get('heatScore') or raw.get('score') or 0),
    }


def scrape_city(city_name: str, max_pages: int = 5) -> list[dict]:
    """功能说明：爬取指定城市的景点数据。"""
    config = CITY_CONFIG.get(city_name)
    if not config:
        print(f'未找到城市 "{city_name}" 的配置，支持的城市：{", ".join(CITY_CONFIG.keys())}')
        return []

    print(f'开始爬取 {city_name} 景点数据...')
    all_attractions = []

    for page in range(1, max_pages + 1):
        print(f'  正在请求第 {page} 页...')
        html = fetch_attraction_page(config['city_pinyin'], config['city_id'], page)
        if not html:
            continue

        page_attractions = parse_attraction_list(html)
        print(f'  第 {page} 页解析到 {len(page_attractions)} 个景点')
        all_attractions.extend(page_attractions)

        time.sleep(1.5)

    print(f'{city_name} 共爬取 {len(all_attractions)} 个景点')
    return all_attractions


def save_to_json(attractions: list[dict], output_path: str) -> None:
    """功能说明：将景点数据保存为 JSON 文件。"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(attractions, f, ensure_ascii=False, indent=2)
    print(f'数据已保存到 {output_path}')


def generate_sql_insert(attractions: list[dict], city_name: str) -> str:
    """功能说明：生成景点数据的 SQL INSERT 语句。"""
    lines = [f'-- {city_name}景点数据（共 {len(attractions)} 条）']
    for attr in attractions:
        name_escaped = attr['name'].replace("'", "\\'")
        area_escaped = attr.get('area', '').replace("'", "\\'")
        tags_escaped = attr.get('tags', '').replace("'", "\\'")
        image_escaped = attr.get('image', '').replace("'", "\\'")
        url_escaped = attr.get('detail_url', '').replace("'", "\\'")
        price_escaped = attr.get('actual_price', '暂无').replace("'", "\\'")
        desc_escaped = attr.get('preferential_desc', '').replace("'", "\\'")
        price_type_desc_escaped = attr.get('price_type_desc', '').replace("'", "\\'")
        distance_escaped = attr.get('distance', '').replace("'", "\\'")

        lines.append(
            f"INSERT INTO `attraction` (`poi_id`, `area`, `name`, `comment_count`, `score`, "
            f"`is_advertisement`, `is_recommend`, `city_name`, `image`, `distance`, `tags`, "
            f"`detail_url`, `market_price`, `preferential_price`, `preferential_desc`, "
            f"`actual_price`, `price_type`, `price_type_desc`, `is_free`, `longitude`, `6`, `heat_score`) VALUES ("
            f"{attr['poi_id']}, "
            f"'{area_escaped}', "
            f"'{name_escaped}', "
            f"{attr.get('comment_count') or 'NULL'}, "
            f"{attr.get('score') or 0}, "
            f"{1 if attr.get('is_advertisement') else 0}, "
            f"{1 if attr.get('is_recommend') else 0}, "
            f"'{city_name}', "
            f"'{image_escaped}', "
            f"'{distance_escaped}', "
            f"'{tags_escaped}', "
            f"'{url_escaped}', "
            f"{attr.get('market_price') or 'NULL'}, "
            f"{attr.get('preferential_price') or 'NULL'}, "
            f"'{desc_escaped}', "
            f"'{price_escaped}', "
            f"{attr.get('price_type') or 'NULL'}, "
            f"'{price_type_desc_escaped}', "
            f"{1 if attr.get('is_free') else 0}, "
            f"{attr.get('longitude') or 0}, "
            f"{attr.get('latitude') or 0}, "
            f"{attr.get('heat_score') or 'NULL'}"
            f");"
        )
    return '\n'.join(lines)


def main():
    """功能说明：爬虫脚本入口。"""
    parser = argparse.ArgumentParser(description='携程景点数据爬取')
    parser.add_argument('--city', type=str, required=True, help='城市名称，如：成都')
    parser.add_argument('--pages', type=int, default=5, help='爬取页数，默认 5 页')
    parser.add_argument('--output', type=str, default=None, help='输出 JSON 文件路径')
    args = parser.parse_args()

    attractions = scrape_city(args.city, args.pages)
    if not attractions:
        return

    output_path = args.output or f'data/{args.city}_attractions.json'
    save_to_json(attractions, output_path)

    sql_path = Path(output_path).with_suffix('.sql')
    sql_content = generate_sql_insert(attractions, args.city)
    sql_path.write_text(sql_content, encoding='utf-8')
    print(f'SQL 已保存到 {sql_path}')


if __name__ == '__main__':
    main()