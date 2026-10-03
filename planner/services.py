"""功能说明：AI 路线规划业务服务。"""
from collections.abc import Iterator
from typing import Any

from django.db import transaction
from django.db.models import Prefetch, QuerySet
from django.shortcuts import get_object_or_404

from planner.models import RoutePlan, RoutePlanStop


def clean_planner_form(data: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """功能说明：校验路线规划表单输入。"""
    cleaned_data = {
        'city': data.get('city', '').strip(),
        'origin_location': data.get('origin_location', '').strip(),
        'budget': data.get('budget', '').strip(),
        'travel_time': data.get('travel_time', '').strip(),
        'preferences': data.get('preferences', '').strip(),
    }
    errors = []
    if not cleaned_data['city']:
        errors.append('请输入目的地城市。')
    if not cleaned_data['budget']:
        errors.append('请输入旅行预算。')
    if not cleaned_data['travel_time']:
        errors.append('请输入出行时间。')
    if not cleaned_data['preferences']:
        errors.append('请输入旅行偏好。')
    if len(cleaned_data['city']) > 50:
        errors.append('目的地城市不能超过 50 个字符。')
    if len(cleaned_data['origin_location']) > 200:
        errors.append('出发地点不能超过 200 个字符。')
    if len(cleaned_data['budget']) > 80:
        errors.append('旅行预算不能超过 80 个字符。')
    if len(cleaned_data['travel_time']) > 80:
        errors.append('出行时间不能超过 80 个字符。')
    if len(cleaned_data['preferences']) > 300:
        errors.append('旅行偏好不能超过 300 个字符。')
    return cleaned_data, errors


def create_route_plan(user: Any, cleaned_data: dict[str, str]) -> RoutePlan:
    """功能说明：创建路线规划记录并调用 LangGraph 生成路线。"""
    plan = RoutePlan.objects.create(
        user=user,
        city=cleaned_data['city'],
        origin_location=cleaned_data.get('origin_location', ''),
        budget=cleaned_data['budget'],
        travel_time=cleaned_data['travel_time'],
        preferences=cleaned_data['preferences'],
    )

    try:
        from planner.agent.graph import PlannerConfigError, run_route_planner
    except ImportError as exc:
        _mark_plan_failed(plan, f'AI 规划依赖未安装，请先安装 requirements.txt 中的 LangGraph 相关依赖。{exc}')
        return plan

    try:
        graph_result = run_route_planner(
            city=plan.city,
            budget=plan.budget,
            travel_time=plan.travel_time,
            preferences=plan.preferences,
            origin_location=plan.origin_location,
        )
    except PlannerConfigError as exc:
        _mark_plan_failed(plan, str(exc))
        return plan
    except Exception as exc:
        _mark_plan_failed(plan, f'AI 路线规划失败：{exc}')
        return plan

    save_route_plan_result(plan, graph_result)
    return plan


def stream_route_plan_events(user: Any, cleaned_data: dict[str, str]) -> Iterator[dict[str, Any]]:
    """功能说明：流式创建路线规划并逐步返回页面展示事件。"""
    plan = RoutePlan.objects.create(
        user=user,
        city=cleaned_data['city'],
        origin_location=cleaned_data.get('origin_location', ''),
        budget=cleaned_data['budget'],
        travel_time=cleaned_data['travel_time'],
        preferences=cleaned_data['preferences'],
    )
    yield {'event': 'started', 'data': {'plan_id': plan.id}}

    try:
        from planner.agent.graph import PlannerConfigError, stream_route_planner
    except ImportError as exc:
        _mark_plan_failed(plan, f'AI 规划依赖未安装，请先安装 requirements.txt 中的 LangGraph 相关依赖。{exc}')
        yield {'event': 'error', 'data': {'message': plan.error_message, 'plan_id': plan.id}}
        return

    try:
        graph_result = {}
        for event_payload in stream_route_planner(
            city=plan.city,
            budget=plan.budget,
            travel_time=plan.travel_time,
            preferences=plan.preferences,
            origin_location=plan.origin_location,
        ):
            if event_payload.get('event') == 'graph_done':
                graph_result = event_payload.get('data', {})
                continue
            yield event_payload
        save_route_plan_result(plan, graph_result)
    except PlannerConfigError as exc:
        _mark_plan_failed(plan, str(exc))
        yield {'event': 'error', 'data': {'message': plan.error_message, 'plan_id': plan.id}}
        return
    except Exception as exc:
        _mark_plan_failed(plan, f'AI 路线规划失败：{exc}')
        yield {'event': 'error', 'data': {'message': plan.error_message, 'plan_id': plan.id}}
        return

    yield {
        'event': 'done',
        'data': {
            'plan_id': plan.id,
            'status': plan.status,
            'final_plan': plan.final_plan,
            'process_steps': plan.process_steps,
            'map_stops': serialize_route_stops(plan),
        },
    }


def save_route_plan_result(plan: RoutePlan, graph_result: dict[str, Any]) -> None:
    """功能说明：保存 LangGraph 生成的路线规划结果。"""
    with transaction.atomic():
        plan.intent_data = graph_result.get('intent', {})
        plan.process_steps = graph_result.get('process_steps', [])
        plan.final_plan = graph_result.get('final_plan', '')
        plan.status = RoutePlan.STATUS_SUCCESS
        plan.error_message = ''
        plan.save(update_fields=['intent_data', 'process_steps', 'final_plan', 'status', 'error_message'])
        _replace_plan_stops(plan, graph_result.get('route_stops', []))


def get_user_plan(user: Any, plan_id: int) -> RoutePlan:
    """功能说明：查询当前用户有权限查看的路线规划记录。"""
    return get_object_or_404(
        RoutePlan.objects.prefetch_related(
            Prefetch('stops', queryset=RoutePlanStop.objects.select_related('attraction'))
        ).select_related('user'),
        pk=plan_id,
        user=user,
    )


def get_recent_plans(user: Any, limit: int = 5) -> QuerySet:
    """功能说明：查询当前用户最近生成的路线规划记录。"""
    return RoutePlan.objects.filter(user=user).order_by('-created_at')[:limit]


def delete_user_plan(user: Any, plan_id: int) -> None:
    """功能说明：删除当前用户的路线规划记录。"""
    plan = get_object_or_404(RoutePlan, pk=plan_id, user=user)
    plan.delete()


def serialize_route_stops(plan: RoutePlan) -> list[dict[str, Any]]:
    """功能说明：将路线站点序列化为前端地图可直接使用的数据。"""
    return [
        {
            'day_index': stop.day_index,
            'sequence': stop.sequence,
            'name': stop.name,
            'city_name': stop.city_name,
            'longitude': stop.longitude,
            'latitude': stop.latitude,
            'image': _get_stop_image(stop),
            'banner_url': _get_stop_banner(stop),
            'score': _get_stop_score(stop),
            'intro': stop.intro,
        }
        for stop in plan.stops.all()
    ]


def _get_stop_image(stop: RoutePlanStop) -> str:
    """功能说明：获取路线站点关联景点的图片地址。"""
    if stop.attraction and stop.attraction.image:
        return stop.attraction.image
    return ''


def _get_stop_banner(stop: RoutePlanStop) -> str:
    """功能说明：获取路线站点关联景点的横幅图片地址。"""
    if stop.attraction and stop.attraction.banner_url:
        return stop.attraction.banner_url
    return ''


def _get_stop_score(stop: RoutePlanStop) -> str:
    """功能说明：获取路线站点关联景点的评分。"""
    if stop.attraction and stop.attraction.score:
        return str(stop.attraction.score)
    return ''


def _mark_plan_failed(plan: RoutePlan, error_message: str) -> None:
    """功能说明：将路线规划记录标记为失败状态。"""
    plan.status = RoutePlan.STATUS_FAILED
    plan.error_message = error_message[:300]
    plan.process_steps = [
        {'title': '规划失败', 'description': plan.error_message, 'status': 'failed'},
    ]
    plan.save(update_fields=['status', 'error_message', 'process_steps'])


def _replace_plan_stops(plan: RoutePlan, route_stops: list[dict[str, Any]]) -> None:
    """功能说明：用新的路线站点替换规划记录下的旧站点。"""
    plan.stops.all().delete()

    stop_objects = []
    for index, stop in enumerate(route_stops, start=1):
        longitude = float(stop.get('longitude') or 0)
        latitude = float(stop.get('latitude') or 0)
        if not longitude or not latitude:
            continue
        stop_objects.append(
            RoutePlanStop(
                plan=plan,
                attraction_id=stop.get('attraction_id'),
                day_index=int(stop.get('day_index') or 1),
                sequence=int(stop.get('sequence') or index),
                name=str(stop.get('name') or ''),
                city_name=str(stop.get('city_name') or plan.city),
                longitude=longitude,
                latitude=latitude,
                intro=str(stop.get('intro') or ''),
            )
        )
    RoutePlanStop.objects.bulk_create(stop_objects)