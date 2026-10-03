"""功能说明：AI 路线规划视图。"""
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from planner.amap_service import geocode, get_multi_strategy_routes, regeo
from planner.models import RoutePlan
from planner.services import clean_planner_form, create_route_plan, get_user_plan, get_recent_plans, stream_route_plan_events, delete_user_plan


@login_required
def planner_view(request: HttpRequest) -> HttpResponse:
    """功能说明：展示 AI 路线规划助手页面。"""
    recent_plans = get_recent_plans(request.user)
    return render(request, 'planner/planner.html', {
        'recent_plans': recent_plans,
        'AMAP_WEB_KEY': getattr(settings, 'AMAP_WEB_KEY', ''),
    })


@login_required
@require_POST
def planner_submit_view(request: HttpRequest) -> HttpResponse:
    """功能说明：提交路线规划请求，支持 SSE 流式和同步两种模式。"""
    data = {
        'city': request.POST.get('city', ''),
        'origin_location': request.POST.get('origin_location', ''),
        'budget': request.POST.get('budget', ''),
        'travel_time': request.POST.get('travel_time', ''),
        'preferences': request.POST.get('preferences', ''),
    }
    cleaned_data, errors = clean_planner_form(data)
    if errors:
        return JsonResponse({'error': errors[0]}, status=400)

    accept_sse = request.headers.get('Accept', '') == 'text/event-stream'

    if accept_sse:
        return StreamingHttpResponse(
            _sse_stream_generator(request.user, cleaned_data),
            content_type='text/event-stream',
        )

    plan = create_route_plan(request.user, cleaned_data)
    return JsonResponse(
        {
            'plan_id': plan.id,
            'status': plan.status,
            'final_plan': plan.final_plan,
            'error_message': plan.error_message,
        }
    )


def _sse_stream_generator(user, cleaned_data):
    """功能说明：将 LangGraph 流式事件转换为 SSE 格式。"""
    for event_payload in stream_route_plan_events(user, cleaned_data):
        event_name = event_payload.get('event', 'message')
        event_data = event_payload.get('data', {})
        yield f'event: {event_name}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n'


@login_required
def planner_result_view(request: HttpRequest, plan_id: int) -> HttpResponse:
    """功能说明：展示路线规划结果详情。"""
    plan = get_user_plan(request.user, plan_id)
    return render(request, 'planner/planner_result.html', {
        'plan': plan,
        'AMAP_WEB_KEY': getattr(settings, 'AMAP_WEB_KEY', ''),
    })


@require_GET
def api_geocode(request: HttpRequest) -> JsonResponse:
    """功能说明：地址转经纬度代理接口，保护高德 Web 服务 Key。"""
    address = request.GET.get('address', '').strip()
    city = request.GET.get('city', '').strip()
    if not address:
        return JsonResponse({'ok': False, 'msg': '请输入地址'}, status=400)

    location = geocode(address, city)
    if location:
        formatted_address = regeo(location) or address
        return JsonResponse({'ok': True, 'location': location, 'formatted_address': formatted_address})
    return JsonResponse({'ok': False, 'msg': '无法解析该地址'}, status=400)


@require_GET
def api_regeo(request: HttpRequest) -> JsonResponse:
    """功能说明：经纬度转地址代理接口。"""
    location = request.GET.get('location', '').strip()
    if not location or ',' not in location:
        return JsonResponse({'ok': False, 'msg': '请提供有效的经纬度（格式：经度,纬度）'}, status=400)

    formatted_address = regeo(location)
    if formatted_address:
        return JsonResponse({'ok': True, 'location': location, 'formatted_address': formatted_address})
    return JsonResponse({'ok': False, 'msg': '无法解析该位置'}, status=400)


@require_GET
def api_transit_routes(request: HttpRequest) -> JsonResponse:
    """功能说明：获取多种换乘策略的公交/地铁路线方案。"""
    origin = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    city = request.GET.get('city', '').strip()

    if not origin or not destination:
        return JsonResponse({'ok': False, 'msg': '请提供起点和终点'}, status=400)

    if ',' not in origin:
        origin = geocode(origin, city) or ''
    if ',' not in destination:
        destination = geocode(destination, city) or ''

    if not origin or not destination:
        return JsonResponse({'ok': False, 'msg': '起点或终点地址无法解析为坐标'}, status=400)

    routes = get_multi_strategy_routes(origin, destination, city)
    return JsonResponse({'ok': True, 'routes': routes, 'origin': origin, 'destination': destination})


@login_required
@require_POST
def planner_delete_view(request: HttpRequest, plan_id: int) -> HttpResponse:
    """功能说明：删除路线规划记录。"""
    delete_user_plan(request.user, plan_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})

    return redirect('planner:planner')