"""功能说明：攻略应用视图。"""
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from guides.models import TravelGuide, TravelGuideImage, TravelGuideAttraction
from guides.services import search_guides, get_city_options, get_guide_detail
from travel.models import Attraction


@login_required
def guide_list_view(request: HttpRequest) -> HttpResponse:
    """功能说明：展示旅游攻略列表并支持搜索筛选。"""
    keyword = request.GET.get('keyword', '').strip()
    city = request.GET.get('city', '').strip()
    page_number = request.GET.get('page', 1)

    guides = search_guides(keyword=keyword, city=city)
    paginator = Paginator(guides, 9)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'guides/guide_list.html',
        {
            'page_obj': page_obj,
            'keyword': keyword,
            'city': city,
            'city_options': get_city_options(),
            'total_count': paginator.count,
        },
    )


@login_required
def guide_detail_view(request: HttpRequest, guide_id: int) -> HttpResponse:
    """功能说明：展示旅游攻略详情。"""
    guide = get_guide_detail(guide_id)
    return render(
        request,
        'guides/guide_detail.html',
        {
            'guide': guide,
            'guide_images': guide.images.all(),
            'guide_attractions': guide.guide_attractions.all(),
        },
    )


@login_required
def guide_create_view(request: HttpRequest) -> HttpResponse:
    """功能说明：创建旅游攻略。"""
    if request.method != 'POST':
        return render(request, 'guides/guide_create.html')

    title = request.POST.get('title', '').strip()
    city = request.POST.get('city', '').strip()
    summary = request.POST.get('summary', '').strip()
    content = request.POST.get('content', '').strip()
    attraction_ids = request.POST.getlist('attraction_ids')
    images = request.FILES.getlist('images')

    errors = []
    if not title:
        errors.append('请输入攻略标题。')
    if not city:
        errors.append('请输入目的地城市。')
    if not content:
        errors.append('请输入攻略正文。')

    if errors:
        return render(request, 'guides/guide_create.html', {'errors': errors})

    guide = TravelGuide.objects.create(
        author=request.user,
        title=title,
        city=city,
        summary=summary,
        content=content,
    )

    for index, image_file in enumerate(images, start=1):
        TravelGuideImage.objects.create(guide=guide, image=image_file, sort_order=index)

    if attraction_ids:
        valid_attractions = Attraction.objects.filter(pk__in=attraction_ids)
        for attraction in valid_attractions:
            TravelGuideAttraction.objects.create(guide=guide, attraction=attraction)

    return redirect('guides:guide_detail', guide_id=guide.pk)


@login_required
def attraction_search_view(request: HttpRequest) -> HttpResponse:
    """功能说明：搜索景点供攻略创建页面选择。"""
    keyword = request.GET.get('keyword', '').strip()
    city = request.GET.get('city', '').strip()

    queryset = Attraction.objects.filter(is_advertisement=False)
    if keyword:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(tags__icontains=keyword) | Q(area__icontains=keyword)
        )
    if city:
        queryset = queryset.filter(city_name__icontains=city)

    attractions = queryset.order_by('-heat_score', '-score')[:20]
    data = [
        {
            'id': a.pk,
            'name': a.name,
            'city_name': a.city_name,
            'area': a.area or '',
            'score': a.score or 0,
            'image': a.image or '',
        }
        for a in attractions
    ]
    return JsonResponse(data, safe=False)