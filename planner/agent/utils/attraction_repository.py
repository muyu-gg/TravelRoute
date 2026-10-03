"""功能说明：AI 路线规划景点数据查询工具。"""
from typing import Any

from django.db.models import Q

from planner.agent.utils.route_utils import parse_budget_amount, rank_candidate_dicts, split_preferences
from travel.models import Attraction


def find_candidate_attractions(city: str, preferences: str, budget: str, limit: int = 16) -> list[dict[str, Any]]:
    """功能说明：根据城市、偏好和预算查询候选景点。"""
    queryset = Attraction.objects.filter(city_name__icontains=city, is_advertisement=False)

    preference_query = Q()
    for keyword in split_preferences(preferences):
        preference_query |= Q(name__icontains=keyword) | Q(tags__icontains=keyword) | Q(area__icontains=keyword)
    if preference_query:
        preferred_queryset = queryset.filter(preference_query)
        if preferred_queryset.count() >= 4:
            queryset = preferred_queryset

    budget_amount = parse_budget_amount(budget)
    if '免费' in budget or '低预算' in budget or budget_amount == 0:
        free_queryset = queryset.filter(is_free=True)
        if free_queryset.exists():
            queryset = free_queryset

    raw_candidates = queryset.order_by('-heat_score', '-score', '-comment_count', 'id')[: max(limit * 3, limit)]
    candidates = [_serialize_attraction(attraction) for attraction in raw_candidates]
    return rank_candidate_dicts(candidates, preferences, budget)[:limit]


def _serialize_attraction(attraction: Attraction) -> dict[str, Any]:
    """功能说明：将景点模型转换为 Agent 工具使用的字典。"""
    return {
        'id': attraction.id,
        'poi_id': attraction.poi_id,
        'name': attraction.name,
        'area': attraction.area or '',
        'city_name': attraction.city_name,
        'comment_count': attraction.comment_count or 0,
        'score': attraction.score or 0,
        'image': attraction.image or '',
        'banner_url': attraction.banner_url or '',
        'tags': attraction.tags or '',
        'market_price': attraction.market_price or 0,
        'preferential_price': attraction.preferential_price or 0,
        'actual_price': attraction.actual_price,
        'is_free': attraction.is_free,
        'longitude': attraction.longitude,
        'latitude': attraction.latitude,
        'heat_score': attraction.heat_score or 0,
    }