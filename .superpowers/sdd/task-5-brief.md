## Task 5: 创建 notify.py 通知模块

**Files:**
- Create: `notify.py`

**Interfaces:**
- Consumes: 无
- Produces: `send_notification(title, message, gotify_host, gotify_token)` 函数

- [ ] **Step 1: 创建 notify.py 文件**

```python
import logging
from gotify import Gotify

logger = logging.getLogger(__name__)


def send_notification(title, message, gotify_host, gotify_token):
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
        logger.info("通知发送成功")
        return True
    except Exception as e:
        logger.error(f"通知发送失败：{e}")
        return False
```

- [ ] **Step 2: 提交文件**

```bash
git add notify.py
git commit -m "feat: 添加通知模块 notify.py"
```
