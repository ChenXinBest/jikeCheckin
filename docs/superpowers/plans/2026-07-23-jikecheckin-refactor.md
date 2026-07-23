# 极客云签到重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将单文件签到脚本重构为模块化结构，支持本地 .env 配置和 GitHub Actions 自动签到。

**Architecture:** 拆分为 3 个核心文件（config.py、notify.py、main.py），通过环境变量统一管理配置，使用 logging 模块输出日志。

**Tech Stack:** Python 3.11, requests, gotify, python-dotenv

## Global Constraints

- Python 版本：3.11+
- 依赖：仅 requests、gotify、python-dotenv
- 配置：通过环境变量读取，本地使用 .env 文件
- 日志：使用 logging 模块，格式为 `%(asctime)s [%(levelname)s] %(message)s`
- 环境变量命名：JIKE_EMAIL, JIKE_PASSWORD, GOTIFY_HOST, GOTIFY_TOKEN, LOG_LEVEL

---

## Task 1: 创建 .gitignore 文件

**Files:**
- Create: `.gitignore`

**Interfaces:**
- Consumes: 无
- Produces: 忽略规则文件

- [ ] **Step 1: 创建 .gitignore 文件**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.local

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

- [ ] **Step 2: 提交文件**

```bash
git add .gitignore
git commit -m "chore: 添加 .gitignore 文件"
```

---

## Task 2: 创建 .env.example 配置模板

**Files:**
- Create: `.env.example`

**Interfaces:**
- Consumes: 无
- Produces: 配置模板文件

- [ ] **Step 1: 创建 .env.example 文件**

```bash
# 极客云账号配置（必填）
JIKE_EMAIL=your_email@example.com
JIKE_PASSWORD=your_password

# Gotify 通知配置（可选）
GOTIFY_HOST=https://gotify.example.com
GOTIFY_TOKEN=your_app_token

# 日志级别（可选，默认 INFO）
# 可选值：DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

- [ ] **Step 2: 提交文件**

```bash
git add .env.example
git commit -m "chore: 添加 .env.example 配置模板"
```

---

## Task 3: 精简 requirements.txt

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: 无
- Produces: 精简后的依赖清单

- [ ] **Step 1: 替换 requirements.txt 内容**

```txt
requests>=2.31.0
gotify>=0.5.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: 提交文件**

```bash
git add requirements.txt
git commit -m "chore: 精简 requirements.txt，仅保留必要依赖"
```

---

## Task 4: 创建 config.py 配置模块

**Files:**
- Create: `config.py`

**Interfaces:**
- Consumes: 无
- Produces: `get_config() -> dict` 函数

- [ ] **Step 1: 创建 config.py 文件**

```python
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
            - gotify_host (str|None): Gotify 服务器地址
            - gotify_token (str|None): Gotify 应用 Token
            - log_level (str): 日志级别，默认 INFO
    """
    jike_email = os.environ.get("JIKE_EMAIL")
    jike_password = os.environ.get("JIKE_PASSWORD")
    
    if not jike_email or not jike_password:
        print("错误：缺少必要配置 JIKE_EMAIL 或 JIKE_PASSWORD")
        print("请复制 .env.example 为 .env 并填写配置")
        sys.exit(1)
    
    return {
        "jike_email": jike_email,
        "jike_password": jike_password,
        "gotify_host": os.environ.get("GOTIFY_HOST"),
        "gotify_token": os.environ.get("GOTIFY_TOKEN"),
        "log_level": os.environ.get("LOG_LEVEL", "INFO").upper(),
    }
```

- [ ] **Step 2: 提交文件**

```bash
git add config.py
git commit -m "feat: 添加配置管理模块 config.py"
```

---

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

---

## Task 6: 创建 main.py 主程序

**Files:**
- Create: `main.py`
- Delete: `jikeCheckin.py`

**Interfaces:**
- Consumes: 
  - `config.get_config() -> dict`
  - `notify.send_notification(title, message, gotify_host, gotify_token) -> bool`
- Produces: 可执行的签到程序

- [ ] **Step 1: 创建 main.py 文件**

```python
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
        bool: 签到成功返回 True，失败返回 False
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
    
    if result.get("ret") == 1:
        msg = result.get("msg", "签到成功")
        logger.info(f"签到成功：{msg}")
        send_notification(
            "签到成功",
            msg,
            config.get("gotify_host"),
            config.get("gotify_token"),
        )
        return True
    else:
        msg = result.get("msg", "签到失败")
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
```

- [ ] **Step 2: 删除旧文件 jikeCheckin.py**

```bash
git rm jikeCheckin.py
```

- [ ] **Step 3: 提交文件**

```bash
git add main.py
git commit -m "feat: 重构主程序为 main.py，支持模块化配置和日志"
```

---

## Task 7: 更新 GitHub Actions 工作流

**Files:**
- Create: `.github/workflows/checkin.yml`
- Delete: `.github/workflows/jikeWork.yml`

**Interfaces:**
- Consumes: 无
- Produces: 修复后的 CI/CD 工作流

- [ ] **Step 1: 创建新的工作流文件 .github/workflows/checkin.yml**

```yaml
name: Jike Checkin

on:
  schedule:
    - cron: '30 16 * * *'  # UTC 16:30 = 北京时间 00:30
  workflow_dispatch:        # 支持手动触发

jobs:
  checkin:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run checkin
        env:
          JIKE_EMAIL: ${{ secrets.JIKE_EMAIL }}
          JIKE_PASSWORD: ${{ secrets.JIKE_PASSWORD }}
          GOTIFY_HOST: ${{ secrets.GOTIFY_HOST }}
          GOTIFY_TOKEN: ${{ secrets.GOTIFY_TOKEN }}
          LOG_LEVEL: INFO
        run: python main.py
```

- [ ] **Step 2: 删除旧的工作流文件**

```bash
git rm .github/workflows/jikeWork.yml
```

- [ ] **Step 3: 提交文件**

```bash
git add .github/workflows/checkin.yml
git commit -m "ci: 更新 GitHub Actions 工作流，修复路径和依赖"
```

---

## Task 8: 重写 README.md

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: 无
- Produces: 开源友好的文档

- [ ] **Step 1: 替换 README.md 内容**

```markdown
# 极客云签到

自动签到极客云，支持本地运行和 GitHub Actions 定时执行。

## 功能特性

- ✅ 自动登录签到
- ✅ 支持 Gotify 通知
- ✅ 本地运行 + GitHub Actions 定时任务
- ✅ 结构化日志输出
- ✅ 失败自动重试（最多 3 次）

## 快速开始

### 方式一：GitHub Actions（推荐）

1. Fork 本仓库

2. 配置 Secrets
   - 进入仓库 Settings → Secrets and variables → Actions
   - 添加以下 Secrets：
     - `JIKE_EMAIL`：极客云邮箱
     - `JIKE_PASSWORD`：极客云密码
     - `GOTIFY_HOST`：Gotify 服务器地址（可选）
     - `GOTIFY_TOKEN`：Gotify 应用 Token（可选）

3. 运行签到
   - 手动触发：Actions → Jike Checkin → Run workflow
   - 自动执行：每天北京时间 00:30 自动签到

### 方式二：本地运行

1. 克隆仓库
   ```bash
   git clone https://github.com/your-username/jikeCheckin.git
   cd jikeCheckin
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量
   ```bash
   cp .env.example .env
   ```
   编辑 `.env` 文件，填写你的极客云账号信息：
   ```
   JIKE_EMAIL=your_email@example.com
   JIKE_PASSWORD=your_password
   ```

4. 运行签到
   ```bash
   python main.py
   ```

## 配置说明

| 变量名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| JIKE_EMAIL | 极客云邮箱 | 是 | - |
| JIKE_PASSWORD | 极客云密码 | 是 | - |
| GOTIFY_HOST | Gotify 服务器地址 | 否 | - |
| GOTIFY_TOKEN | Gotify 应用 Token | 否 | - |
| LOG_LEVEL | 日志级别（DEBUG/INFO/WARNING/ERROR） | 否 | INFO |

## 日志输出示例

```
2024-01-15 10:30:15 [INFO] 极客云签到开始
2024-01-15 10:30:15 [INFO] 第 1/3 次尝试
2024-01-15 10:30:15 [INFO] 正在登录...
2024-01-15 10:30:16 [INFO] 登录成功，正在签到...
2024-01-15 10:30:17 [INFO] 签到成功：获得 10 积分
2024-01-15 10:30:17 [INFO] 通知发送成功
2024-01-15 10:30:17 [INFO] 签到完成
```

## 项目结构

```
jikeCheckin/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── notify.py            # 通知模块
├── .env.example         # 配置模板
├── requirements.txt     # 依赖清单
└── .github/workflows/
    └── checkin.yml      # GitHub Actions 工作流
```

## 常见问题

### Q: 如何修改签到时间？

编辑 `.github/workflows/checkin.yml`，修改 `cron` 表达式：

```yaml
schedule:
  - cron: '30 16 * * *'  # UTC 时间，北京时间 = UTC + 8
```

### Q: 如何禁用 Gotify 通知？

不配置 `GOTIFY_HOST` 和 `GOTIFY_TOKEN` 即可，程序会自动跳过通知。

### Q: 签到失败怎么办？

1. 检查账号密码是否正确
2. 检查网络是否正常
3. 查看日志输出，定位具体错误
4. 程序会自动重试最多 3 次

## License

MIT
```

- [ ] **Step 2: 提交文件**

```bash
git add README.md
git commit -m "docs: 重写 README.md，添加使用说明和配置文档"
```

---

## Task 9: 清理旧文件并验证

**Files:**
- Modify: 无（验证任务）

**Interfaces:**
- Consumes: 所有已创建的文件
- Produces: 验证结果

- [ ] **Step 1: 验证项目结构**

```bash
ls -la
```

预期输出：
```
.git/
.github/
docs/
main.py
config.py
notify.py
.env.example
.gitignore
requirements.txt
README.md
```

- [ ] **Step 2: 验证依赖安装**

```bash
pip install -r requirements.txt
```

预期：安装成功，无错误

- [ ] **Step 3: 验证配置检查**

```bash
python main.py
```

预期输出（未配置 .env 时）：
```
错误：缺少必要配置 JIKE_EMAIL 或 JIKE_PASSWORD
请复制 .env.example 为 .env 并填写配置
```

- [ ] **Step 4: 检查 git 状态**

```bash
git status
git log --oneline -10
```

预期：所有文件已提交，无未跟踪文件

---

## 完成标准

- [ ] 所有文件已创建并提交
- [ ] 项目结构符合设计文档
- [ ] 本地可以运行 `python main.py`
- [ ] GitHub Actions 工作流配置正确
- [ ] README.md 包含完整使用说明
- [ ] .gitignore 正确忽略 .env 文件
