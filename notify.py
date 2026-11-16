"""通知模块。

支持两个渠道：
- Gotify：兼容原有行为，标题 + 正文；
- WXPUSH：标题为 "✓成功" / "×失败"，正文为 "获得流量：{流量}；执行用时：{用时}"。

各渠道独立判断配置是否完整，配置完整的渠道才会收到消息；
任意一个渠道失败都不会影响其他渠道。
"""

import logging

import requests
from gotify import Gotify

logger = logging.getLogger(__name__)

# WXPUSH 标题
WXPUSH_TITLE_SUCCESS = "✓成功"
WXPUSH_TITLE_FAILURE = "×失败"

# WXPUSH 请求头（部分网关会拦截无浏览器特征的请求）
WXPUSH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}

WXPUSH_TIMEOUT = 15


def send_gotify(title, message, gotify_host=None, gotify_token=None):
    """
    发送 Gotify 通知。

    Args:
        title (str): 通知标题
        message (str): 通知内容
        gotify_host (str|None): Gotify 服务器地址
        gotify_token (str|None): Gotify 应用 Token

    Returns:
        bool: 发送成功返回 True，未配置或失败返回 False
    """
    if not gotify_host or not gotify_token:
        logger.debug("Gotify 未配置，跳过通知")
        return False

    try:
        client = Gotify(base_url=gotify_host, app_token=gotify_token)
        client.create_message(
            title=title,
            message=message,
            priority=0,
        )
        logger.info("Gotify 通知发送成功")
        return True
    except Exception as e:
        logger.error(f"Gotify 通知发送失败：{e}")
        return False


def send_wxpush(title, content, wxpush_base_url=None, wxpush_userid=None, wxpush_template_id=None):
    """
    发送 WXPUSH 通知。

    通过 GET 请求把 userid / template_id / content / title 放在查询参数中。

    Args:
        title (str): 通知标题（✓成功 / ×失败）
        content (str): 通知内容
        wxpush_base_url (str|None): WXPUSH 推送地址
        wxpush_userid (str|None): WXPUSH 用户 ID
        wxpush_template_id (str|None): WXPUSH 模板 ID

    Returns:
        bool: 发送成功返回 True，未配置或失败返回 False
    """
    if not wxpush_base_url or not wxpush_userid or not wxpush_template_id:
        logger.debug("WXPUSH 未配置完整，跳过通知")
        return False

    params = {
        "userid": wxpush_userid,
        "template_id": wxpush_template_id,
        "content": content,
        "title": title,
    }

    try:
        response = requests.get(
            wxpush_base_url,
            params=params,
            headers=WXPUSH_HEADERS,
            timeout=WXPUSH_TIMEOUT,
        )
    except Exception as e:
        logger.error(f"WXPUSH 通知发送失败：{e}")
        return False

    if response.status_code != 200:
        logger.error(f"WXPUSH 通知发送失败：HTTP {response.status_code}")
        return False

    if not _is_wxpush_success(response):
        logger.error(f"WXPUSH 通知发送失败：{response.text.strip()[:200]}")
        return False

    logger.info(f"WXPUSH 通知发送成功：{response.text.strip()[:200]}")
    return True


def _is_wxpush_success(response):
    """
    判断 WXPUSH 响应是否表示成功。

    响应为 JSON 且带 code/errcode 字段时按状态码判断（0、200 视为成功），
    其余情况以 HTTP 200 为准。
    """
    try:
        data = response.json()
    except ValueError:
        return True

    if isinstance(data, dict):
        for key in ("code", "errcode", "errno"):
            if key not in data:
                continue
            try:
                return int(data[key]) in (0, 200)
            except (TypeError, ValueError):
                return True
    return True


def send_notifications(config, success, title, message, traffic="0MB", elapsed="0s"):
    """
    按渠道分发通知。

    Args:
        config (dict): 配置字典
        success (bool): 本次签到是否成功（决定 WXPUSH 标题）
        title (str): Gotify 通知标题
        message (str): Gotify 通知内容
        traffic (str): 获得的流量，如 "666MB"
        elapsed (str): 脚本执行用时，如 "12s"

    Returns:
        list[str]: 发送成功的渠道名称列表
    """
    sent = []

    if send_gotify(
        title,
        message,
        config.get("gotify_host"),
        config.get("gotify_token"),
    ):
        sent.append("gotify")

    wxpush_title = WXPUSH_TITLE_SUCCESS if success else WXPUSH_TITLE_FAILURE
    wxpush_content = f"获得流量：{traffic}；执行用时：{elapsed}"
    if send_wxpush(
        wxpush_title,
        wxpush_content,
        config.get("wxpush_base_url"),
        config.get("wxpush_userid"),
        config.get("wxpush_template_id"),
    ):
        sent.append("wxpush")

    return sent


def send_notification(title, message, gotify_host=None, gotify_token=None):
    """兼容旧接口：仅发送 Gotify 通知。"""
    return send_gotify(title, message, gotify_host, gotify_token)
