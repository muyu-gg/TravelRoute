"""功能说明：DeepSeek 大模型调用工具。"""
from collections.abc import Iterator
from typing import Any

from django.conf import settings


class PlannerConfigError(Exception):
    """功能说明：表示 AI 路线规划配置缺失或不可用。"""


def get_deepseek_client():
    """功能说明：创建 DeepSeek OpenAI 兼容客户端。"""
    from openai import OpenAI

    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    if not api_key:
        raise PlannerConfigError('未配置 DEEPSEEK_API_KEY，请在环境变量中填写后再使用 AI 路线规划助手。')

    return OpenAI(api_key=api_key, base_url=getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com'))


def get_deepseek_chat_model(streaming: bool = False):
    """功能说明：创建支持 LangGraph 工具绑定的 DeepSeek ChatOpenAI 模型。"""
    from langchain_openai import ChatOpenAI

    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    if not api_key:
        raise PlannerConfigError('未配置 DEEPSEEK_API_KEY，请在环境变量或 .env 文件中填写后再使用 AI 路线规划助手。')

    return ChatOpenAI(
        api_key=api_key,
        base_url=getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        model=getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat'),
        temperature=0,
        streaming=streaming,
    )


def call_deepseek_chat(messages: list[dict[str, str]]) -> str:
    """功能说明：调用 DeepSeek Chat Completions 并返回文本内容。"""
    client = get_deepseek_client()
    model_name = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=False,
    )

    content: Any = response.choices[0].message.content
    return str(content or '').strip()