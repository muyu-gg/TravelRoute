"""功能说明：AI 路线规划路线构建与验证工具。"""
import math
import re
from typing import Any, Optional


def parse_budget_amount(budget: str) -> Optional[float]:
    """功能说明：从预算文本中提取可以用于排序的数字金额。"""
    match = re.search(r'\d+(?:\.\d+)?', budget)
    if not match:
        return None
    return float(match.group())


def parse_travel_days(travel_time: str) -> int:
    """功能说明：从出行时间文本中提取旅行天数。"""
    match = re.search(r'(\d+)\s*天', travel_time)
    if match:
        return max(1, min(int(match.group(1)), 10))

    if "周末" in travel_time:
        return 2
    if "一日" in travel_time or '一天' in travel_time or '当天' in travel_time:
        return 1
    return 1


def split_preferences(preferences: str) -> list[str]:
    """功能说明：将旅行偏好文本拆分为关键词列表。"""
    raw_words = re.split(r'[\s,，、/；;]+', preferences)
    return [word.strip() for word in raw_words if word.strip()]


def normalize_float(value: Any, default: float = 0.0) -> float:
    """功能说明：将数据库或工具值安全转换为浮点数。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def rank_candidate_dicts(
    candidates: list[dict[str, Any]],
    preferences: str,
    budget: str,
) -> list[dict[str, Any]]:
    """功能说明：根据偏好、预算、评分和热度对候选景点排序。"""
    keywords = split_preferences(preferences)
    budget_amount = parse_budget_amount(budget)

    def score_candidate(candidate: dict[str, Any]) -> float:
        """功能说明：计算单个候选景点的排序分值。"""
        score = normalize_float(candidate.get('score')) * 12
        score += normalize_float(candidate.get('heat_score')) * 0.8
        score += min(normalize_float(candidate.get('comment_count')), 5000) / 500

        search_text = f"{candidate.get('name', '')} {candidate.get('area', '')} {candidate.get('tags', '')}"
        for keyword in keywords:
            if keyword and keyword in search_text:
                score += 8

        price = normalize_float(candidate.get('preferential_price') or candidate.get('market_price'))
        if candidate.get('is_free'):
            score += 6
        elif budget_amount is not None and price and price <= budget_amount:
            score += 3
        elif budget_amount is not None and price and price > budget_amount:
            score -= 6
        return score

    return sorted(candidates, key=score_candidate, reverse=True)


def build_route_stops(
    candidates: list[dict[str, Any]],
    travel_time: str,
    budget: str,
    preferences: str,
) -> list[dict[str, Any]]:
    """功能说明：根据候选景点生成带天数和顺序的路线站点。"""
    days = parse_travel_days(travel_time)
    max_stops = max(2, min(days * 4, 12))
    ranked_candidates = rank_candidate_dicts(candidates, preferences, budget)[:max_stops]

    ordered_candidates = _order_by_nearest_neighbor(ranked_candidates)
    route_stops = []
    for index, candidate in enumerate(ordered_candidates, start=1):
        route_stops.append(
            {
                'attraction_id': candidate.get('id'),
                'day_index': min(days, math.ceil(index / 4)),
                'sequence': ((index - 1) % 4) + 1,
                'name': candidate.get('name', ''),
                'city_name': candidate.get('city_name', ''),
                'longitude': normalize_float(candidate.get('longitude')),
                'latitude': normalize_float(candidate.get('latitude')),
                'image': candidate.get('image', ''),
                'banner_url': candidate.get('banner_url', ''),
                'score': candidate.get('score', ''),
                'intro': build_stop_intro(candidate, preferences),
            }
        )
    return route_stops


def validate_route_plan_quality(
    route_stops: list[dict[str, Any]],
    budget: str,
    travel_time: str,
    preferences: str,
) -> dict[str, Any]:
    """功能说明：检查路线是否符合用户要求并评估折返风险。"""
    expected_days = parse_travel_days(travel_time)
    issues = []
    suggestions = []
    optimized_route_stops = _optimize_route_stops_by_day(route_stops)

    if not route_stops:
        return {
            'is_valid': False,
            'score': 0,
            'issues': ['没有生成可用景点站点。'],
            'suggestions': ['请扩大目的地范围或放宽旅行偏好。'],
            'optimized_route_stops': [],
            'distance_ratio': 0,
        }

    max_reasonable_stops = max(2, expected_days * 4)
    if len(route_stops) > max_reasonable_stops:
        issues.append(f'当前路线包含 {len(route_stops)} 个站点，超过 {expected_days} 天行程的合理承载数量。')
        suggestions.append('建议减少部分低优先级景点，避免行程过赶。')

    max_day_index = max(int(stop.get('day_index') or 1) for stop in route_stops)
    if max_day_index > expected_days:
        issues.append(f'路线安排到第 {max_day_index} 天，超过用户输入的 {expected_days} 天。')
        suggestions.append('建议压缩或重新分配每日站点。')

    preference_result = _check_preference_coverage(route_stops, preferences)
    if not preference_result['is_matched']:
        issues.append('路线站点与用户旅行偏好的匹配度偏低。')
        suggestions.append('建议提高偏好关键词相关景点的优先级。')

    budget_result = _check_budget_friendliness(route_stops, budget)
    if not budget_result['is_budget_friendly']:
        issues.append('当前路线对低预算用户不够友好。')
        suggestions.append('建议增加免费或低门票景点。')

    distance_ratio = _calculate_distance_ratio(route_stops, optimized_route_stops)
    if distance_ratio > 1.35:
        issues.append(f'路线折返指数为 {distance_ratio:.2f}，存在较多来回折返。')
        suggestions.append('建议按地图距离重新排序，减少跨区域往返。')
    else:
        optimized_route_stops = route_stops

    score = max(0, 100 - len(issues) * 18)
    return {
        'is_valid': len(issues) == 0,
        'score': score,
        'issues': issues,
        'suggestions': suggestions,
        'optimized_route_stops': optimized_route_stops,
        'distance_ratio': round(distance_ratio, 2),
        'preference_match_count': preference_result['match_count'],
        'budget_free_count': budget_result['free_count'],
    }


def build_stop_intro(candidate: dict[str, Any], preferences: str) -> str:
    """功能说明：生成路线站点的简短介绍。"""
    tags = candidate.get('tags') or '城市热门景点'
    score = normalize_float(candidate.get('score'))
    price_text = '免费游览' if candidate.get('is_free') else f"门票参考：{candidate.get('actual_price') or '暂无'}"
    return f'{tags}，评分 {score:.1f}，{price_text}，适合偏好「{preferences}」的行程安排。'


def _order_by_nearest_neighbor(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """功能说明：使用最近邻策略对景点进行空间顺序排序。"""
    if len(candidates) <= 1:
        return candidates

    remaining = candidates[:]
    ordered = [remaining.pop(0)]
    while remaining:
        current = ordered[-1]
        next_candidate = min(remaining, key=lambda item: _coordinate_distance(current, item))
        ordered.append(next_candidate)
        remaining.remove(next_candidate)
    return ordered


def _coordinate_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    """功能说明：计算两个景点经纬度的近似距离。"""
    left_lng = normalize_float(left.get('longitude'))
    left_lat = normalize_float(left.get('latitude'))
    right_lng = normalize_float(right.get('longitude'))
    right_lat = normalize_float(right.get('latitude'))
    return (left_lng - right_lng) ** 2 + (left_lat - right_lat) ** 2


def _check_preference_coverage(route_stops: list[dict[str, Any]], preferences: str) -> dict[str, Any]:
    """功能说明：检查路线站点是否覆盖用户旅行偏好。"""
    keywords = [keyword for keyword in split_preferences(preferences) if len(keyword) >= 2]
    if not keywords:
        return {'is_matched': True, 'match_count': 0}

    route_text = ' '.join(f"{stop.get('name', '')} {stop.get('intro', '')}" for stop in route_stops)
    match_count = sum(1 for keyword in keywords if keyword in route_text)
    required_count = max(1, min(2, len(keywords)))
    return {'is_matched': match_count >= required_count, 'match_count': match_count}


def _check_budget_friendliness(route_stops: list[dict[str, Any]], budget: str) -> dict[str, Any]:
    """功能说明：检查路线是否适合低预算用户。"""
    budget_amount = parse_budget_amount(budget)
    is_low_budget = budget_amount is not None and budget_amount <= 300
    is_free_preference = '免费' in budget or '低预算' in budget or '省钱' in budget
    if not is_low_budget and not is_free_preference:
        return {'is_budget_friendly': True, 'free_count': 0}

    free_count = sum(1 for stop in route_stops if '免费' in str(stop.get('intro', '')))
    return {'is_budget_friendly': free_count > 0, 'free_count': free_count}


def _optimize_route_stops_by_day(route_stops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """功能说明：按每天内部距离重新排序路线站点。"""
    grouped_stops: dict[int, list[dict[str, Any]]] = {}
    for stop in route_stops:
        day_index = int(stop.get('day_index') or 1)
        grouped_stops.setdefault(day_index, []).append(dict(stop))

    optimized_stops = []
    for day_index in sorted(grouped_stops):
        ordered_stops = _order_stops_by_nearest_neighbor(grouped_stops[day_index])
        for sequence, stop in enumerate(ordered_stops, start=1):
            stop['day_index'] = day_index
            stop['sequence'] = sequence
            optimized_stops.append(stop)
    return optimized_stops


def _order_stops_by_nearest_neighbor(stops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """功能说明：使用最近邻策略对路线站点排序。"""
    if len(stops) <= 1:
        return stops

    remaining = stops[:]
    ordered = [remaining.pop(0)]
    while remaining:
        current = ordered[-1]
        next_stop = min(remaining, key=lambda item: _coordinate_distance(current, item))
        ordered.append(next_stop)
        remaining.remove(next_stop)
    return ordered


def _calculate_distance_ratio(
    route_stops: list[dict[str, Any]],
    optimized_route_stops: list[dict[str, Any]],
) -> float:
    """功能说明：计算原路线距离与优化路线距离的比值。"""
    original_distance = _calculate_route_distance(route_stops)
    optimized_distance = _calculate_route_distance(optimized_route_stops)
    if optimized_distance <= 0:
        return 1.0
    return original_distance / optimized_distance


def _calculate_route_distance(route_stops: list[dict[str, Any]]) -> float:
    """功能说明：计算路线在每天内部的近似总距离。"""
    grouped_stops: dict[int, list[dict[str, Any]]] = {}
    for stop in route_stops:
        day_index = int(stop.get('day_index') or 1)
        grouped_stops.setdefault(day_index, []).append(stop)

    total_distance = 0.0
    for day_stops in grouped_stops.values():
        for index in range(1, len(day_stops)):
            total_distance += math.sqrt(_coordinate_distance(day_stops[index - 1], day_stops[index]))
    return total_distance