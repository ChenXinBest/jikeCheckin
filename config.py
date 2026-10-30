import os
import sys
from dotenv import load_dotenv

load_dotenv()


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
            - log_level (str): 日志级别，默认 INFO
    """
    jike_email = os.environ.get("JIKE_EMAIL")
    jike_password = os.environ.get("JIKE_PASSWORD")
    # 代理：优先 JIKE_PROXY，其次标准 HTTP_PROXY / HTTPS_PROXY（requests 会自动读取）
    jike_proxy = os.environ.get("JIKE_PROXY") or os.environ.get("HTTPS_PROXY")
    
    if not jike_email or not jike_password:
        print("错误：缺少必要配置 JIKE_EMAIL 或 JIKE_PASSWORD")
        print("请复制 .env.example 为 .env 并填写配置")
        sys.exit(1)
    
    return {
        "jike_email": jike_email,
        "jike_password": jike_password,
        "jike_proxy": jike_proxy,
        "gotify_host": os.environ.get("GOTIFY_HOST"),
        "gotify_token": os.environ.get("GOTIFY_TOKEN"),
        "log_level": os.environ.get("LOG_LEVEL", "INFO").upper(),
    }
