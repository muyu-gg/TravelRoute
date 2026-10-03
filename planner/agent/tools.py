"""功能说明：AI 路线规划 LangGraph 工具。"""
from langchain_core.tools import tool

from planner.agent.utils.attraction_repository import find_candidate_attractions
from planner.agent.utils.json_utils import dump_json, extract_json_object, load_json_dict
from planner.agent.utils.llm import call_deepseek_chat
from planner.agent.utils.prompt_utils import build_intent_messages
from planner.agent.utils.route_utils import build_route_stops, validate_route_plan_quality


@tool
def parse_travel_intent(city: str, budget: str, travel_time: str, preferences: str, origin_location: str = '') -> str:
    """功能说明：调用大模型识别用户旅游路线规划意图。"""
    messages = build_intent_messages(
        city=city,
        budget=budget,
        travel_time=travel_time,
        preferences=preferences,
        origin_location=origin_location,
    )
    content = call_deepseek_chat(messages)

    intent = extract_json_object(content)
    return dump_json(intent)


@tool
def search_attractions(city: str, preferences: str, budget: str, limit: int = 16) -> str:
    """功能说明：根据城市、旅行偏好和预算检索可用于路线规划的候选景点。"""
    attractions = find_candidate_attractions(city=city, preferences=preferences, budget=budget, limit=limit)
    return dump_json({'attractions': attractions, 'count': len(attractions)})


@tool
def build_route_candidates(attractions_json: str, travel_time: str, budget: str, preferences: str) -> str:
    """功能说明：根据候选景点、出行时间、预算和偏好生成有顺序的路线站点。"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"🔧 build_route_candidates 被调用")
    logger.info(f"   - attractions_json 类型: {type(attractions_json)}")
    logger.info(f"   - attractions_json 长度: {len(str(attractions_json)) if attractions_json else 0}")
    logger.info(f"   - travel_time: {travel_time}")
    logger.info(f"   - budget: {budget}")
    logger.info(f"   - preferences: {preferences}")

    if not attractions_json:
        logger.error("❌ attractions_json 为空！")
        return dump_json({'route_stops': [], 'count': 0, 'error': 'attractions_json 参数为空'})

    try:
        payload = load_json_dict(attractions_json)
        logger.info(f"   - 解析后的 payload keys: {payload.keys() if payload else 'None'}")

        attractions = payload.get('attractions', [])
        if not isinstance(attractions, list):
            logger.warning(f"⚠️ attractions 不是列表: {type(attractions)}")
            attractions = []

        logger.info(f"   - 候选景点数量: {len(attractions)}")

        route_stops = build_route_stops(
            candidates=attractions,
            travel_time=travel_time,
            budget=budget,
            preferences=preferences,
        )

        logger.info(f"✅ 成功生成 {len(route_stops)} 个路线站点")
        return dump_json({'route_stops': route_stops, 'count': len(route_stops)})

    except Exception as e:
        logger.error(f"❌ build_route_candidates 执行失败: {e}", exc_info=True)
        return dump_json({'route_stops': [], 'count': 0, 'error': str(e)})


@tool
def validate_route_plan(route_stops_json: str, travel_time: str, budget: str, preferences: str) -> str:
    """功能说明：检查路线是否符合用户要求，并评估是否存在明显来回折返。"""
    payload = load_json_dict(route_stops_json)
    route_stops = payload.get('route_stops', [])
    if not isinstance(route_stops, list):
        route_stops = []

    validation_result = validate_route_plan_quality(
        route_stops=route_stops,
        travel_time=travel_time,
        budget=budget,
        preferences=preferences,
    )
    return dump_json(validation_result)


def get_planner_tools() -> list:
    """功能说明：返回 LangGraph ToolNode 需要注册的工具列表。"""
    return [parse_travel_intent, search_attractions, build_route_candidates, validate_route_plan]