import logging
import sys
import requests
from config import get_config
from notify import send_notification

logger = logging.getLogger(__name__)

# 站点（nginx + Cloudflare）会拦截不带浏览器特征的请求，
# 直接用 requests 默认 UA 访问 /auth/login 会收到 403 Forbidden，
# 表现为“登录失败/账号密码错误”，实际与账号密码无关。
# 因此使用 fake-useragent 随机生成真实的桌面端 User-Agent。
FALLBACK_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
MOBILE_HINTS = ("Mobile", "Android", "iPhone", "iPad", "Tablet", "Silk")
DESKTOP_BROWSERS = ["Chrome", "Firefox", "Edge", "Safari"]
DESKTOP_OS = ["Windows", "Mac OS X", "Linux"]

BASE_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://jike138.com",
    "Referer": "https://jike138.com/auth/login",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _random_user_agent():
    """从 fake-useragent 库随机取一个 User-Agent（不做过滤）。"""
    from fake_useragent import UserAgent

    try:
        # fake-useragent >= 2.x 支持按浏览器/系统/平台过滤
        ua = UserAgent(
            browsers=DESKTOP_BROWSERS,
            os=DESKTOP_OS,
            platforms=["desktop"],
        )
    except TypeError:
        # fake-useragent 1.x 构造参数不同，退化为无参构造
        ua = UserAgent()

    return ua.random


def get_user_agent(max_attempts=10):
    """
    获取一个随机且合法的桌面端 User-Agent。

    Args:
        max_attempts (int): 最多随机尝试次数

    Returns:
        str: User-Agent 字符串
    """
    agent = None
    for _ in range(max_attempts):
        try:
            agent = _random_user_agent()
        except Exception as e:
            logger.warning(f"获取随机 User-Agent 失败：{e}")
            break
        if agent and not any(h in agent for h in MOBILE_HINTS):
            return agent

    logger.info("使用默认 User-Agent")
    return FALLBACK_USER_AGENT


def setup_logging(level_name):
    """配置日志格式和级别。"""
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class JikeCheckin:
    """极客云签到客户端。"""
    
    BASE_URL = "https://jike138.com"
    
    def __init__(self, email, password, proxy=None):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self.user_agent = get_user_agent()
        self.session.headers.update({"User-Agent": self.user_agent})
        logger.info(f"User-Agent：{self.user_agent}")
        if proxy:
            self.session.proxies.update({"http": proxy, "https": proxy})
            logger.info(f"已启用代理：{proxy}")

    def _get_login_page(self):
        """访问登录页，拿到服务端下发的 Cookie（uid/email 等）。"""
        try:
            self.session.get(f"{self.BASE_URL}/auth/login", timeout=15)
        except Exception as e:
            logger.warning(f"获取登录页失败（忽略）：{e}")

    def _parse_json(self, response, action):
        """
        解析响应。

        站点出错时可能返回 403/5xx 的 HTML，此时给出明确提示，
        避免把拦截误判成“账号密码错误”。
        """
        if response.status_code != 200:
            body = response.text[:200].replace("\n", " ")
            logger.error(f"{action} HTTP {response.status_code}：{body}")
            raise RuntimeError(f"{action} HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError:
            body = response.text[:200].replace("\n", " ")
            logger.error(f"{action}返回非 JSON 内容：{body}")
            raise RuntimeError(f"{action}返回非 JSON 内容")

    def login(self):
        """
        登录极客云。
        
        Returns:
            bool: 登录成功返回 True，失败返回 False
        """
        url = f"{self.BASE_URL}/auth/login"
        data = {
            "email": self.email,
            "passwd": self.password,
            "code": "",
            "remember_me": "on",
        }

        try:
            self._get_login_page()
            response = self.session.post(url, data=data, timeout=15)
            result = self._parse_json(response, "登录")
            ret = result.get("ret")
            msg = result.get("msg", "")
            if ret == 1:
                logger.info(f"登录成功：{msg}")
                return True
            if ret == 2:
                logger.error("该账号启用了两步验证（2FA），需要填写验证码，脚本暂不支持")
                return False
            logger.error(f"登录失败：{msg or '未知错误'}")
            return False
        except Exception as e:
            logger.error(f"登录请求失败：{e}")
            return False
    
    def checkin(self):
        """
        执行签到。
        
        Returns:
            dict: 签到结果，包含 ret 和 msg 字段
        """
        url = f"{self.BASE_URL}/user/checkin"

        try:
            response = self.session.post(
                url,
                headers={"Referer": f"{self.BASE_URL}/user"},
                timeout=15,
            )
            return self._parse_json(response, "签到")
        except Exception as e:
            logger.error(f"签到请求失败：{e}")
            return {"ret": 0, "msg": str(e)}


def run(config):
    """
    执行签到流程。

    Args:
        config (dict): 配置字典

    Returns:
        bool: 签到成功返回 True（包括已签到），失败返回 False
    """
    client = JikeCheckin(
        config["jike_email"],
        config["jike_password"],
        proxy=config.get("jike_proxy"),
    )
    
    logger.info("正在登录...")
    if not client.login():
        logger.error("登录失败")
        send_notification(
            "登录失败",
            "极客云签到登录失败，请检查账号密码或网络/代理配置",
            config.get("gotify_host"),
            config.get("gotify_token"),
        )
        return False
    
    logger.info("登录成功，正在签到...")
    result = client.checkin()
    msg = result.get("msg", "")
    
    if result.get("ret") == 1 or "已经签到" in msg:
        logger.info(f"签到成功：{msg}")
        send_notification(
            "签到成功",
            msg,
            config.get("gotify_host"),
            config.get("gotify_token"),
        )
        return True
    else:
        logger.warning(f"签到失败：{msg}")
        send_notification(
            "签到失败",
            msg,
            config.get("gotify_host"),
            config.get("gotify_token"),
        )
        return False


def main():
    """主入口函数。"""
    config = get_config()
    setup_logging(config["log_level"])
    
    logger.info("极客云签到开始")
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        logger.info(f"第 {attempt}/{max_retries} 次尝试")
        if run(config):
            logger.info("签到完成")
            return
        if attempt < max_retries:
            logger.info("准备重试...")
    
    logger.error("签到失败，已达最大重试次数")
    sys.exit(1)


if __name__ == "__main__":
    main()
