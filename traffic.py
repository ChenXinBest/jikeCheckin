"""流量解析工具。

从签到消息或账户面板文本中提取流量数值，例如 "666MB"、"1.5GB"。
"""

import re

# 数值 + 单位
_NUMBER = r"\d+(?:\.\d+)?"
_UNIT = r"(?:TB|GB|MB|KB|T|G|M|B)"

# 带「流量」关键词的写法优先匹配
_PATTERNS = (
    # 获得 666MB 流量 / 666 MB流量
    re.compile(rf"({_NUMBER})\s*({_UNIT})\s*(?:的)?\s*流量", re.IGNORECASE),
    # 流量：666MB / 剩余流量 666MB
    re.compile(
        rf"(?:剩余|可用|已用|获得)?\s*流量\s*[:：]?\s*(?:剩余|可用|获得)?\s*({_NUMBER})\s*({_UNIT})",
        re.IGNORECASE,
    ),
)

# 兜底：文本提到「流量」时，取第一个带单位的数值（优先 GB/MB 等大单位）
_FALLBACK_PATTERN = re.compile(rf"({_NUMBER})\s*({_UNIT})", re.IGNORECASE)


def parse_traffic(text):
    """
    从文本中提取流量数值。

    Args:
        text (str): 待解析文本（签到消息或页面 HTML）

    Returns:
        str|None: 形如 "666MB" 的流量字符串，未找到时返回 None
    """
    if not text:
        return None

    normalized = re.sub(r"<[^>]+>", " ", str(text))
    normalized = normalized.replace("&nbsp;", " ").replace("&amp;", "&")
    normalized = re.sub(r"\s+", " ", normalized)

    for pattern in _PATTERNS:
        match = pattern.search(normalized)
        if match:
            return _format(match.group(1), match.group(2))

    if "流量" in normalized:
        match = _FALLBACK_PATTERN.search(normalized)
        if match:
            return _format(match.group(1), match.group(2))

    return None


def _format(number, unit):
    """拼接数值与单位，如 ("666", "mb") -> "666MB"。"""
    return f"{number}{unit.upper()}"
