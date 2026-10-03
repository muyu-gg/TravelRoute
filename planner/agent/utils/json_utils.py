"""功能说明：AI 路线规划 JSON 工具函数。"""
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def dump_json(data: Any) -> str:
    """功能说明：将数据序列化为 JSON 字符串。"""
    return json.dumps(data, ensure_ascii=False, default=str)


def extract_json_object(text: str) -> dict[str, Any]:
    """功能说明：从文本中提取第一个 JSON 对象。"""
    start = text.find('{')
    if start == -1:
        return {}
    depth = 0
    for index in range(start, len(text)):
        if text[index] == '{':
            depth += 1
        elif text[index] == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:index + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


def load_json_dict(text: str) -> dict[str, Any]:
    """功能说明：将 JSON 字符串解析为字典（增强容错版）。"""
    if not text or not text.strip():
        logger.warning("load_json_dict: 输入为空")
        return {}

    text = text.strip()

    # 尝试1：直接解析
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
        logger.warning(f"load_json_dict: JSON 不是字典类型: {type(result)}")
    except json.JSONDecodeError as e:
        logger.debug(f"load_json_dict: 直接解析失败: {e}")

    # 尝试2：提取JSON对象
    result = extract_json_object(text)
    if result:
        return result

    # 尝试3：修复常见的JSON格式问题
    fixed_text = _fix_common_json_issues(text)
    if fixed_text != text:
        try:
            result = json.loads(fixed_text)
            if isinstance(result, dict):
                logger.info("load_json_dict: 修复后成功解析")
                return result
        except json.JSONDecodeError:
            pass

    # 尝试4：提取数组并包装
    array_result = _extract_and_wrap_array(text)
    if array_result:
        return array_result

    logger.warning(f"load_json_dict: 所有解析尝试均失败，输入长度: {len(text)}")
    logger.debug(f"load_json_dict: 输入内容前100字符: {text[:100]}")
    return {}


def _fix_common_json_issues(text: str) -> str:
    """功能说明：修复常见的JSON格式问题。"""
    import re

    # 移除单行注释
    text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)

    # 移除多行注释
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # 修复尾随逗号
    text = re.sub(r',\s*([}\]])', r'\1', text)

    # 修复单引号为双引号
    text = re.sub(r"'([^']*)'", r'"\1"', text)

    # 修复None/True/False为JSON格式
    text = text.replace('None', 'null').replace('True', 'true').replace('False', 'false')

    return text


def _extract_and_wrap_array(text: str) -> dict[str, Any]:
    """功能说明：提取JSON数组并包装成字典。"""
    start = text.find('[')
    if start == -1:
        return {}

    depth = 0
    for index in range(start, len(text)):
        if text[index] == '[':
            depth += 1
        elif text[index] == ']':
            depth -= 1
            if depth == 0:
                try:
                    array_data = json.loads(text[start:index + 1])
                    if isinstance(array_data, list):
                        return {'attractions': array_data}
                except json.JSONDecodeError:
                    pass
                break

    return {}