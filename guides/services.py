"""功能说明：攻略应用业务服务。"""
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet

from guides.models import TravelGuide


def build_guide_queryset() -> QuerySet:
    """功能说明：构造攻略基础查询集，预加载关联数据。"""
    return TravelGuide.objects.select_related('author').prefetch_related('images', 'guide_attractions__attraction')


def search_guides(keyword: str = '', city: str = '') -> QuerySet:
    """功能说明：根据关键词和城市搜索攻略。"""
    guides = build_guide_queryset().order_by('-created_at')
    if keyword:
        guides = guides.filter(
            Q(title__icontains=keyword) | Q(summary__icontains=keyword) | Q(content__icontains=keyword)
        )
    if city:
        guides = guides.filter(city=city)
    return guides


def get_city_options() -> QuerySet:
    """功能说明：获取攻略中出现的城市列表。"""
    return TravelGuide.objects.values_list('city', flat=True).distinct().order_by('city')


def get_guide_detail(guide_id: int) -> TravelGuide:
    """功能说明：查询攻略详情并增加浏览量。"""
    guide = build_guide_queryset().get(pk=guide_id)
    TravelGuide.objects.filter(pk=guide_id).update(view_count=guide.view_count + 1)
    guide.refresh_from_db()
    return guide