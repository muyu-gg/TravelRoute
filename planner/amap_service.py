"""功能说明：高德地图 Web 服务 API 封装，提供地理编码、逆地理编码、公交路径规划等能力。"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

AMAP_WEB_KEY = os.environ.get('AMAP_SERVER_KEY', '')

_REQUEST_TIMEOUT = 8


def _get(path: str, params: dict) -> dict:
    """功能说明：调用高德 Web 服务 API 的通用 GET 请求。"""
    if not AMAP_WEB_KEY:
        logger.warning('AMAP_SERVER_KEY 未配置，高德地图服务不可用。')
        return {'status': '0', 'info': 'AMAP_SERVER_KEY not configured'}

    params = {**params, 'key': AMAP_WEB_KEY}
    url = f'https://restapi.amap.com{path}'
    try:
        resp = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error(f'高德 API 请求失败: {url} {exc}')
        return {'status': '0', 'info': str(exc)}


def geocode(address: str, city: str = '') -> str | None:
    """功能说明：地址转经纬度，返回 "经度,纬度" 字符串。"""
    data = _get('/v3/geocode/geo', {'address': address, 'city': city})
    if data.get('status') == '1' and data.get('geocodes'):
        return data['geocodes'][0]['location']
    return None


def regeo(location: str) -> str | None:
    """功能说明：经纬度转结构化地址。"""
    data = _get('/v3/geocode/regeo', {'location': location})
    if data.get('status') == '1':
        return data['regeocode']['formatted_address']
    return None


def ip_location(ip: str = '') -> dict:
    """功能说明：IP 定位，返回省份、城市和经纬度。"""
    params = {}
    if ip:
        params['ip'] = ip
    data = _get('/v5/ip', params)
    if data.get('status') == '1':
        return {
            'province': data.get('province', ''),
            'city': data.get('city', ''),
            'location': data.get('location', ''),
        }
    return {}


def transit_route(origin: str, destination: str, city: str, strategy: int = 0) -> dict:
    """功能说明：公交/地铁/综合换乘路径规划。

    strategy: 0推荐 1最经济 2最少换乘 3最少步行 4最舒适 5不乘地铁 6地铁图 7地铁优先 8时间最短
    """
    return _get('/v3/direction/transit/integrated', {
        'origin': origin,
        'destination': destination,
        'city': city,
        'strategy': strategy,
    })


def driving_route(origin: str, destination: str) -> dict:
    """功能说明：驾车路径规划。"""
    return _get('/v5/direction/driving', {
        'origin': origin,
        'destination': destination,
    })


def walking_route(origin: str, destination: str) -> dict:
    """功能说明：步行路径规划。"""
    return _get('/v5/direction/walking', {
        'origin': origin,
        'destination': destination,
    })


STRATEGY_LABELS = {
    0: '推荐方案',
    1: '最经济',
    2: '最少换乘',
    3: '最少步行',
    6: '地铁图',
    7: '地铁优先',
    8: '时间最短',
}


def parse_transit_lines(route_json: dict) -> list[dict]:
    """功能说明：从高德公交路径规划返回中提炼地铁/公交线路。"""
    result = []
    transits = route_json.get('route', {}).get('transits', [])
    for plan in transits:
        segs = []
        for seg in plan.get('segments', []):
            bus = seg.get('bus', {})
            for line in bus.get('buslines', []):
                segs.append({
                    'is_metro': '地铁' in (line.get('type') or '') or '地铁' in (line.get('name') or ''),
                    'line_name': line.get('name', ''),
                    'from_stop': (bus.get('departure_stop') or {}).get('name', ''),
                    'to_stop': (bus.get('arrival_stop') or {}).get('name', ''),
                    'distance_m': line.get('distance'),
                    'duration_s': line.get('duration'),
                    'polyline': line.get('polyline'),
                })
            walking = seg.get('walking')
            if walking:
                segs.append({
                    'is_metro': False,
                    'line_name': '步行',
                    'distance_m': walking.get('distance'),
                    'duration_s': walking.get('duration'),
                    'polyline': walking.get('polyline'),
                })
        result.append({
            'duration_s': plan.get('duration'),
            'cost': plan.get('cost'),
            'distance': plan.get('distance'),
            'segments': segs,
        })
    return result


def get_multi_strategy_routes(origin: str, destination: str, city: str) -> list[dict]:
    """功能说明：获取多种换乘策略的公交路线方案。"""
    strategies = [0, 2, 7, 8]
    results = []
    for strategy in strategies:
        raw = transit_route(origin, destination, city, strategy)
        plans = parse_transit_lines(raw)
        if plans:
            best = plans[0]
            best['strategy'] = strategy
            best['strategy_label'] = STRATEGY_LABELS.get(strategy, f'策略{strategy}')
            results.append(best)
    return results