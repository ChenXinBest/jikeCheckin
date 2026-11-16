import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _env(name, default=None):
    """
    读取环境变量。

    空字符串视为未配置（GitHub Actions 中未设置的 Secret 会是空字符串）。

    Args:
        name (str): 环境变量名
        default: 未配置时的默认值

    Returns:
        str|None: 环境变量值
    """
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def get_config():
    """
    读取配置并返回配置字典。

    Returns:
        dict: 包含以下键的配置字典
            - jike_email (str): 极客云邮箱
            - jike_password (str): 极客云密码
            - jike_proxy (str|None): 代理地址（可选）
            - gotify_host (str|None): Gotify 服务器地址
            - gotify_token (str|None): Gotify 应用 Token
            - wxpush_base_url (str|None): WXPUSH 推送地址（不填则不启用该渠道）
            - wxpush_userid (str|None): WXPUSH 用户 ID
            - wxpush_template_id (str|None): WXPUSH 模板 ID
            - log_level (str): 日志级别，默认 INFO
    """
    jike_email = _env("JIKE_EMAIL")
    jike_password = _env("JIKE_PASSWORD")
    # 代理：优先 JIKE_PROXY，其次标准 HTTP_PROXY / HTTPS_PROXY（requests 会自动读取）
    jike_proxy = _env("JIKE_PROXY") or _env("HTTPS_PROXY")

    if not jike_email or not jike_password:
        print("错误：缺少必要配置 JIKE_EMAIL 或 JIKE_PASSWORD")
        print("请复制 .env.example 为 .env 并填写配置")
        sys.exit(1)

    return {
        "jike_email": jike_email,
        "jike_password": jike_password,
        "jike_proxy": jike_proxy,
        "gotify_host": _env("GOTIFY_HOST"),
        "gotify_token": _env("GOTIFY_TOKEN"),
        "wxpush_base_url": _env("WXPUSH_BASE_URL"),
        "wxpush_userid": _env("WXPUSH_USERID"),
        "wxpush_template_id": _env("WXPUSH_TEMPLATE_ID"),
        "log_level": (_env("LOG_LEVEL", "INFO") or "INFO").upper(),
    }
