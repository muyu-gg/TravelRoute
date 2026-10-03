"""功能说明：LangGraph 路线规划状态图构建与运行。"""
from collections.abc import Iterator
from typing import Annotated, Any

from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from planner.agent.tools import get_planner_tools
from planner.agent.utils.json_utils import load_json_dict
from planner.agent.utils.llm import get_deepseek_chat_model, PlannerConfigError
from planner.agent.utils.prompt_utils import build_agent_system_message


class PlannerState(TypedDict):
    """功能说明：定义 AI 路线规划 LangGraph Agent 状态。"""

    messages: Annotated[list[AnyMessage], add_messages]
    city: str
    budget: str
    travel_time: str
    preferences: str
    origin_location: str
    intent: dict[str, Any]
    candidates: list[dict[str, Any]]
    route_stops: list[dict[str, Any]]
    validation_result: dict[str, Any]
    final_plan: str
    process_steps: list[dict[str, str]]
    processed_tool_call_ids: list[str]


def _build_initial_state(city: str, budget: str, travel_time: str, preferences: str, origin_location: str = '') -> PlannerState:
    """功能说明：构建 LangGraph Agent 初始状态。"""
    origin_desc = f'、出发地 {origin_location}' if origin_location else ''
    input_step = {
        'title': '输入接收',
        'description': f'已收到目的地 {city}、预算 {budget}、出行时间 {travel_time}{origin_desc} 和旅行偏好。',
        'status': 'success',
    }

    origin_line = f'出发地点：{origin_location}\n' if origin_location else ''
    return {
        'messages': [
            HumanMessage(
                content=(
                    f'请为我规划旅游路线。\n'
                    f'目的地城市：{city}\n'
                    f'{origin_line}'
                    f'预算：{budget}\n'
                    f'出行时间：{travel_time}\n'
                    f'旅行偏好：{preferences}'
                )
            )
        ],
        'city': city,
        'budget': budget,
        'travel_time': travel_time,
        'preferences': preferences,
        'origin_location': origin_location,
        'intent': {},
        'candidates': [],
        'route_stops': [],
        'validation_result': {},
        'final_plan': '',
        'process_steps': [input_step],
        'processed_tool_call_ids': [],
    }


def _build_state_summary(state: PlannerState) -> str:
    """功能说明：构建当前状态摘要供 Agent 系统提示使用。"""
    parts = []
    origin = state.get('origin_location', '')
    if origin:
        parts.append(f'用户出发地：{origin}')
    intent = state.get('intent', {})
    if intent:
        parts.append(f'意图已识别：{intent}')
    else:
        parts.append('意图尚未识别。')

    candidates = state.get('candidates', [])
    parts.append(f'候选景点数量：{len(candidates)}')

    route_stops = state.get('route_stops', [])
    parts.append(f'路线站点数量：{len(route_stops)}')

    validation = state.get('validation_result', {})
    if validation:
        parts.append(f'路线验证结果：有效={validation.get("is_valid")}, 评分={validation.get("score")}')
    else:
        parts.append('路线尚未验证。')

    return '\n'.join(parts)


def _build_agent_messages(state: PlannerState) -> list[AnyMessage]:
    """功能说明：构造 Agent 节点的消息列表。"""
    from langchain_core.messages import SystemMessage

    state_summary = _build_state_summary(state)
    system_message = SystemMessage(content=build_agent_system_message(state_summary))
    return [system_message] + list(state.get('messages', []))


def _message_has_tool_calls(message: Any) -> bool:
    """功能说明：检查消息是否包含工具调用。"""
    return bool(getattr(message, 'tool_calls', None))


def _message_content_to_text(message: Any) -> str:
    """功能说明：将消息内容转换为文本。"""
    content = getattr(message, 'content', '')
    if isinstance(content, list):
        return '\n'.join(str(item) for item in content)
    return str(content or '')


def _resolve_tool_name(message: Any, state: PlannerState) -> str:
    """功能说明：从 ToolMessage 反查工具名称。"""
    tool_call_id = getattr(message, 'tool_call_id', '') or ''
    for msg in state.get('messages', []):
        if _message_has_tool_calls(msg):
            for tool_call in msg.tool_calls:
                if tool_call.get('id') == tool_call_id:
                    return tool_call.get('name', '')
    return ''


def _build_intent_from_payload(payload: dict, state: PlannerState) -> dict:
    """功能说明：从工具返回数据构建意图。"""
    return payload if payload else {'city': state.get('city', ''), 'raw': True}


def _build_intent_step(intent: dict) -> dict[str, str]:
    """功能说明：构建意图识别步骤。"""
    return {'title': '意图识别', 'description': f'已识别目的地 {intent.get("city", "")}，天数 {intent.get("travel_days", "?")}，偏好 {intent.get("preferences", "")}。', 'status': 'success'}


def _build_validation_step(payload: dict) -> dict[str, str]:
    """功能说明：构建路线验证步骤。"""
    is_valid = payload.get('is_valid', False)
    score = payload.get('score', 0)
    status = 'success' if is_valid else 'warning'
    desc = f'路线评分 {score} 分。' + ('验证通过。' if is_valid else '存在可优化项。')
    return {'title': '路线质量检查', 'description': desc, 'status': status}


def _build_agent_decision_step(response: Any, state: PlannerState) -> dict[str, str]:
    """功能说明：构建 Agent 决策步骤。"""
    if _message_has_tool_calls(response):
        tool_names = [tc.get('name', '') for tc in response.tool_calls]
        return {'title': 'Agent 决策', 'description': f'模型决定调用工具：{", ".join(tool_names)}', 'status': 'running'}
    return {'title': 'Agent 完成', 'description': '模型已生成最终路线说明。', 'status': 'success'}


def _agent_node(state: PlannerState) -> dict[str, Any]:
    """功能说明：运行 LLM Agent 节点，由模型自主决定工具调用或结束。"""
    model = get_deepseek_chat_model(streaming=False).bind_tools(get_planner_tools())
    response = model.invoke(_build_agent_messages(state))

    process_steps = list(state.get('process_steps', []))
    process_steps.append(_build_agent_decision_step(response, state))
    result = {'messages': [response], 'process_steps': process_steps}
    if not _message_has_tool_calls(response):
        result['final_plan'] = _message_content_to_text(response)
    return result


def _sync_tool_outputs(state: PlannerState) -> dict[str, Any]:
    """功能说明：解析尚未同步的 ToolNode 输出并更新结构化状态。"""
    processed_tool_call_ids = set(state.get('processed_tool_call_ids', []))
    process_steps = list(state.get('process_steps', []))
    intent = dict(state.get('intent') or {})
    candidates = list(state.get('candidates', []))
    route_stops = list(state.get('route_stops', []))
    validation_result = dict(state.get('validation_result', {}))

    for message in state.get('messages', []):
        if not isinstance(message, ToolMessage):
            continue
        tool_call_id = getattr(message, 'tool_call_id', '') or ''
        if tool_call_id in processed_tool_call_ids:
            continue
        tool_name = _resolve_tool_name(message, state)
        payload = load_json_dict(_message_content_to_text(message))

        if tool_name == 'parse_travel_intent':
            intent = _build_intent_from_payload(payload, state)
            process_steps.append(_build_intent_step(intent))
        elif tool_name == 'search_attractions':
            candidates = payload.get('attractions', [])
            if not isinstance(candidates, list):
                candidates = []
            process_steps.append(
                {'title': '景点检索', 'description': f'工具返回 {len(candidates)} 个候选景点。', 'status': 'success'}
            )
        elif tool_name == 'build_route_candidates':
            route_stops = payload.get('route_stops', [])
            if not isinstance(route_stops, list):
                route_stops = []
            process_steps.append(
                {'title': '路线生成', 'description': f'工具生成 {len(route_stops)} 个地图站点和游览顺序。', 'status': 'success'}
            )
        elif tool_name == 'validate_route_plan':
            validation_result = payload
            optimized_route_stops = payload.get('optimized_route_stops') or route_stops
            if isinstance(optimized_route_stops, list):
                route_stops = optimized_route_stops
            process_steps.append(_build_validation_step(payload))
        processed_tool_call_ids.add(tool_call_id)

    return {
        'intent': intent,
        'candidates': candidates,
        'route_stops': route_stops,
        'validation_result': validation_result,
        'process_steps': process_steps,
        'processed_tool_call_ids': list(processed_tool_call_ids),
    }


def build_route_graph():
    """功能说明：构建标准 LangGraph Tool-calling Agent 图。"""
    workflow = StateGraph(PlannerState)
    workflow.add_node('agent', _agent_node)
    workflow.add_node('tools', ToolNode(get_planner_tools()))
    workflow.add_node('sync', _sync_tool_outputs)
    workflow.add_edge(START, 'agent')
    workflow.add_conditional_edges('agent', tools_condition)
    workflow.add_edge('tools', 'sync')
    workflow.add_edge('sync', 'agent')
    return workflow.compile()


def _build_result_payload(state: PlannerState) -> dict[str, Any]:
    """功能说明：从 LangGraph 状态中提取可保存的路线规划结果。"""
    return {
        'intent': state.get('intent', {}),
        'candidates': state.get('candidates', []),
        'route_stops': state.get('route_stops', []),
        'validation_result': state.get('validation_result', {}),
        'final_plan': state.get('final_plan', ''),
        'process_steps': state.get('process_steps', []),
    }


def run_route_planner(city: str, budget: str, travel_time: str, preferences: str, origin_location: str = '') -> dict[str, Any]:
    """功能说明：运行标准 LangGraph Agent 并返回路线规划结果。"""
    graph = build_route_graph()
    config = {'recursion_limit': 50}
    final_state = graph.invoke(
        _build_initial_state(city, budget, travel_time, preferences, origin_location),
        config=config
    )
    return _build_result_payload(final_state)


def stream_route_planner(city: str, budget: str, travel_time: str, preferences: str, origin_location: str = '') -> Iterator[dict[str, Any]]:
    """功能说明：流式运行标准 LangGraph Agent 并逐步返回规划事件。"""
    graph = build_route_graph()
    state = _build_initial_state(city, budget, travel_time, preferences, origin_location)
    start_step = {'title': '任务启动', 'description': '已收到规划条件，正在启动标准 LangGraph Agent。', 'status': 'running'}
    state['process_steps'] = [start_step] + list(state.get('process_steps', []))
    yielded_step_count = len(state['process_steps'])
    yield {'event': 'step', 'data': start_step}
    yield {'event': 'step', 'data': state['process_steps'][1]}

    final_text_yielded = False
    for chunk in graph.stream(state, stream_mode='values'):
        final_plan = str(chunk.get('final_plan') or '')
        if final_plan and not final_text_yielded:
            final_text_yielded = True
            yield {'event': 'final_start', 'data': {'message': '标准 Agent 已完成工具调用，正在输出最终路线。'}}
            yield {'event': 'final_delta', 'data': {'content': final_plan}}

        for step in chunk.get('process_steps', [])[yielded_step_count:]:
            yielded_step_count += 1
            yield {'event': 'step', 'data': step}
        state = chunk

    if state.get('final_plan') and not final_text_yielded:
        yield {'event': 'final_start', 'data': {'message': '标准 Agent 已生成最终路线。'}}
        yield {'event': 'final_delta', 'data': {'content': state['final_plan']}}
    yield {'event': 'route_stops', 'data': {'route_stops': state.get('route_stops', [])}}
    yield {'event': 'graph_done', 'data': _build_result_payload(state)}