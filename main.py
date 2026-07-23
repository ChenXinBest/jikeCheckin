import logging
import sys
import requests
from config import get_config
from notify import send_notification

logger = logging.getLogger(__name__)


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
    
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
    
    def login(self):
        """
        登录极客云。
        
        Returns:
            bool: 登录成功返回 True，失败返回 False
        """
        url = f"{self.BASE_URL}/auth/login"
        data = {"email": self.email, "passwd": self.password}
        
        try:
            response = self.session.post(url, data=data)
            result = response.json()
            return result.get("ret") == 1
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
            response = self.session.post(url)
            return response.json()
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
    client = JikeCheckin(config["jike_email"], config["jike_password"])
    
    logger.info("正在登录...")
    if not client.login():
        logger.error("登录失败")
        send_notification(
            "登录失败",
            "极客云签到登录失败，请检查账号密码",
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
