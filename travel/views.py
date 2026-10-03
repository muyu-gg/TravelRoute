"""功能说明：景点应用视图。"""
import os

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from travel.models import Attraction, AttractionFavorite, AttractionComment


def build_pagination_items(current: int, total: int, window: int = 2) -> list:
    """功能说明：构建分页导航项列表。"""
    if total <= 1:
        return []
    items = []
    for page in range(1, total + 1):
        if page == 1 or page == total or abs(page - current) <= window:
            items.append({'number': page, 'is_current': page == current, 'is_ellipsis': False})
        elif items and not items[-1]['is_ellipsis']:
            items.append({'number': None, 'is_current': False, 'is_ellipsis': True})
    return items


@login_required
def attraction_list_view(request: HttpRequest) -> HttpResponse:
    """功能说明：展示旅游景点列表并支持关键词、城市和免费条件筛选。"""
    keyword = request.GET.get('keyword', '').strip()
    city = request.GET.get('city', '').strip()
    is_free = request.GET.get('is_free', '').strip()
    page_number = request.GET.get('page', 1)

    attractions = Attraction.objects.all()
    if keyword:
        attractions = attractions.filter(
            Q(name__icontains=keyword) | Q(tags__icontains=keyword) | Q(area__icontains=keyword) | Q(city_name__icontains=keyword)
        )
    if city:
        attractions = attractions.filter(city_name=city)
    if is_free in {'0', '1'}:
        attractions = attractions.filter(is_free=(is_free == '1'))
    attractions = attractions.order_by('-heat_score', '-score', '-comment_count', 'id')

    city_options = Attraction.objects.values_list('city_name', flat=True).distinct().order_by('city_name')
    paginator = Paginator(attractions, 12)
    page_obj = paginator.get_page(page_number)
    pagination_items = build_pagination_items(page_obj.number, paginator.num_pages)

    page_query = request.GET.copy()
    page_query.pop('page', None)
    encoded_page_query = page_query.urlencode()
    page_query_prefix = f'?{encoded_page_query}&' if encoded_page_query else '?'

    return render(
        request,
        'travel/attraction_list.html',
        {
            'page_obj': page_obj,
            'paginator': paginator,
            'keyword': keyword,
            'city': city,
            'is_free': is_free,
            'city_options': city_options,
            'total_count': paginator.count,
            'pagination_items': pagination_items,
            'page_query_prefix': page_query_prefix,
        },
    )


@login_required
def attraction_detail_view(request: HttpRequest, attraction_id: int) -> HttpResponse:
    """功能说明：展示站内旅游景点详情页。"""
    attraction = get_object_or_404(Attraction, pk=attraction_id)

    is_favorited = AttractionFavorite.objects.filter(user=request.user, attraction=attraction).exists()
    favorite_count = AttractionFavorite.objects.filter(attraction=attraction).count()
    comments = (
        AttractionComment.objects.select_related('user')
        .filter(attraction=attraction)
        .order_by('-created_at')
    )

    tag_list = [tag.strip() for tag in attraction.tags.split(',') if tag.strip()] if attraction.tags else []

    return render(
        request,
        'travel/attraction_detail.html',
        {
            'attraction': attraction,
            'is_favorited': is_favorited,
            'favorite_count': favorite_count,
            'comments': comments,
            'tag_list': tag_list,
            'AMAP_JS_KEY': os.environ.get('gaodeMap', ''),
        },
    )


@login_required
def add_comment_view(request: HttpRequest, attraction_id: int) -> HttpResponse:
    """功能说明：为景点添加评论的API接口。"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '仅支持 POST 请求'}, status=405)

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': '评论内容不能为空'}, status=400)

    attraction = get_object_or_404(Attraction, pk=attraction_id)

    comment = AttractionComment.objects.create(
        user=request.user,
        attraction=attraction,
        content=content
    )

    return JsonResponse({
        'success': True,
        'comment_id': comment.id,
        'message': '评论发表成功'
    })


@login_required
def favorite_toggle_view(request: HttpRequest) -> HttpResponse:
    """功能说明：切换用户对景点的收藏状态。"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求。'}, status=405)

    attraction_id = request.POST.get('attraction_id')
    if not attraction_id:
        return JsonResponse({'error': '缺少景点标识。'}, status=400)

    attraction = get_object_or_404(Attraction, pk=attraction_id)
    favorite, created = AttractionFavorite.objects.get_or_create(
        user=request.user, attraction=attraction
    )
    if not created:
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True

    favorite_count = AttractionFavorite.objects.filter(attraction=attraction).count()
    return JsonResponse({'is_favorited': is_favorited, 'favorite_count': favorite_count})


def search_view(request: HttpRequest) -> HttpResponse:
    """功能说明：全局搜索页面。"""
    keyword = request.GET.get('keyword', '').strip()
    attractions = []
    if keyword:
        attractions = Attraction.objects.filter(
            Q(name__icontains=keyword) | Q(tags__icontains=keyword) | Q(city_name__icontains=keyword)
        ).order_by('-heat_score', '-score')[:20]

    return render(request, 'travel/search.html', {'keyword': keyword, 'attractions': attractions})