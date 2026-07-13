# 极客云签到重构与本地运行支持 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 92 行单文件 `jikeCheckin.py` 拆为 4 个职责清晰的模块，新增 Windows / Linux 一键启动脚本和 `.env` 加载机制，保证 GitHub Action 行为不变。

**Architecture:** 根目录 `jikeCheckin.py` 保留为 5 行薄入口（GitHub Action 不动）。新增 `jike_checkin/` 包，按职责拆为 `config` / `client` / `notifier` / `service` 四个模块，外加 `logging_setup` 共 5 个文件，每个 ≤50 行。配置用 `python-dotenv` 加载，env 优先于 `.env`。日志走 `logging` 模块，控制台 INFO + 文件 DEBUG 按天轮转 7 份。

**Tech Stack:** Python 3.10+、`requests`、`gotify`、`python-dotenv`、`pytest`、`pytest-mock`。

## Global Constraints

- Python 版本：≥ 3.10（Action 锁 3.10.12，本地脚本提示用户安装 3.10+）。
- 运行时依赖（写入 `requirements.txt`）：`requests>=2.28`、`gotify==0.5.0`、`python-dotenv>=1.0`。
- 开发依赖（写入 `requirements-dev.txt`）：`-r requirements.txt`、`pytest>=7.0`、`pytest-mock>=3.10`。
- 不创建虚拟环境（保持简单）。
- `.github/workflows/jikeWork.yml` 一字不改；入口路径仍是根目录 `jikeCheckin.py`。
- 不引入 coverage 工具。
- 不为通知渠道抽接口（只有 Gotify 一种）。
- 日志格式：`时间 | 级别 | 模块 | 消息`。
- 日志目录：`logs/jike_checkin.log`，按天轮转，保留 7 份。
- 退出码：0 成功 / 1 业务或配置失败。
- 配置值不写入日志，仅记录字段名。
- 关键行为保持：登录失败重试 ≤3 次（间隔 1 秒）、签到不重试、Gotify `ret == 1` 即成功、`priority=0`。

## File Structure

**新建**：
- `jike_checkin/__init__.py` — 包标记
- `jike_checkin/logging_setup.py` — 日志初始化（控制台 + 文件按天轮转）
- `jike_checkin/config.py` — `Config` dataclass、`ConfigError`、`load_config()`
- `jike_checkin/client.py` — `JikeClient.login() / .checkin()`
- `jike_checkin/notifier.py` — `GotifyNotifier.send()`
- `jike_checkin/service.py` — `RunResult`、`run()`
- `tests/__init__.py` — 测试包标记
- `tests/test_logging_setup.py` — 日志初始化测试
- `tests/test_config.py` — 配置加载测试
- `tests/test_client.py` — HTTP 客户端测试
- `tests/test_notifier.py` — Gotify 通知测试
- `tests/test_service.py` — 业务编排测试
- `tests/test_entry.py` — 根入口文件测试
- `logs/.gitkeep` — 日志目录占位
- `.env.example` — 配置示例
- `requirements-dev.txt` — 开发依赖
- `run.bat` — Windows 启动脚本
- `run.sh` — Linux / macOS 启动脚本

**修改**：
- `jikeCheckin.py`（根）— 替换为 5 行入口
- `requirements.txt` — 新增 `python-dotenv`
- `README.md` — 更新本地使用方法

**保持不动**：
- `.github/workflows/jikeWork.yml`
- `.idea/` 目录

---

## Task 1: 建立包骨架与日志初始化

**Files:**
- Create: `jike_checkin/__init__.py`
- Create: `jike_checkin/logging_setup.py`
- Create: `tests/__init__.py`
- Create: `tests/test_logging_setup.py`
- Create: `logs/.gitkeep`

**Interfaces:**
- Produces: `jike_checkin.logging_setup.init_logging() -> None` — 配置根日志器，幂等（重复调用不重复加 handler）。

- [ ] **Step 1: 创建 `jike_checkin/__init__.py`**

```python
"""极客云签到重构版主包。"""
__version__ = "0.1.0"
```

- [ ] **Step 2: 创建 `tests/__init__.py`**

```python
"""测试包标记文件。"""
```

- [ ] **Step 3: 创建 `logs/.gitkeep`**

创建空文件 `logs/.gitkeep`（目录占位，文件内容为空）。

- [ ] **Step 4: 写失败测试 `tests/test_logging_setup.py`**

```python
import logging
from pathlib import Path

from jike_checkin.logging_setup import init_logging


def test_init_logging_creates_root_logger():
    init_logging()
    logger = logging.getLogger("jike_checkin")
    assert logger.level == logging.DEBUG


def test_init_logging_adds_console_and_file_handlers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_logging()
    logger = logging.getLogger("jike_checkin")
    handlers = logger.handlers
    assert len(handlers) >= 2  # 控制台 + 文件
    assert any(h.__class__.__name__ == "StreamHandler" for h in handlers)
    assert any(h.__class__.__name__ == "TimedRotatingFileHandler" for h in handlers)


def test_init_logging_is_idempotent():
    init_logging()
    n1 = len(logging.getLogger("jike_checkin").handlers)
    init_logging()
    n2 = len(logging.getLogger("jike_checkin").handlers)
    assert n1 == n2


def test_init_logging_writes_to_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_logging()
    logging.getLogger("jike_checkin").info("hello")
    log_file = Path("logs") / "jike_checkin.log"
    assert log_file.exists()
    assert "hello" in log_file.read_text(encoding="utf-8")
```

- [ ] **Step 5: 跑测试确认失败**

```bash
pytest tests/test_logging_setup.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'jike_checkin.logging_setup'`。

- [ ] **Step 6: 实现 `jike_checkin/logging_setup.py`**

```python
"""日志初始化：控制台 INFO + 文件 DEBUG 按天轮转。"""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_LOG_DIR = Path("logs")
_LOG_FILE = _LOG_DIR / "jike_checkin.log"
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_LOGGER_NAME = "jike_checkin"


def init_logging() -> None:
    """配置根日志器；幂等：重复调用不会重复添加 handler。"""
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return

    formatter = logging.Formatter(_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=_LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)
```

- [ ] **Step 7: 跑测试确认通过**

```bash
pytest tests/test_logging_setup.py -v
```

Expected: 4 passed。

- [ ] **Step 8: 提交**

```bash
git add jike_checkin/__init__.py jike_checkin/logging_setup.py tests/__init__.py tests/test_logging_setup.py logs/.gitkeep
git commit -m "feat(jike_checkin): 建立包骨架与日志初始化模块"
```

---

## Task 2: 配置加载模块

**Files:**
- Create: `jike_checkin/config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces:
  - `class ConfigError(Exception)` — 配置错误异常。
  - `@dataclass(frozen=True) class Config` — 含 `email / password / gotify_host / gotify_token / proxies` 字段。
  - `def load_config() -> Config` — 从 env 优先于 `.env` 加载，校验必填项。

- [ ] **Step 1: 写失败测试 `tests/test_config.py`**

```python
import os
from pathlib import Path

import pytest

from jike_checkin.config import Config, ConfigError, load_config


def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("jike_email", "a@b.com")
    monkeypatch.setenv("jike_password", "pw")
    cfg = load_config()
    assert cfg.email == "a@b.com"
    assert cfg.password == "pw"
    assert cfg.gotify_host is None
    assert cfg.gotify_token is None
    assert cfg.proxies is None


def test_load_config_from_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("jike_email", raising=False)
    monkeypatch.delenv("jike_password", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "jike_email=from_env@b.com\n"
        "jike_password=pw_from_env\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.email == "from_env@b.com"
    assert cfg.password == "pw_from_env"


def test_env_overrides_dotenv(tmp_path, monkeypatch):
    monkeypatch.setenv("jike_email", "from_env@b.com")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "jike_email=from_file@b.com\n"
        "jike_password=pw\n",
        encoding="utf-8",
    )
    cfg = load_config()
    assert cfg.email == "from_env@b.com"


def test_missing_email_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("jike_email", raising=False)
    monkeypatch.delenv("jike_password", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("jike_password=pw\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="jike_email"):
        load_config()


def test_missing_password_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("jike_email", raising=False)
    monkeypatch.delenv("jike_password", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("jike_email=a@b.com\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="jike_password"):
        load_config()


def test_proxies_parsed(tmp_path, monkeypatch):
    monkeypatch.setenv("jike_email", "a@b.com")
    monkeypatch.setenv("jike_password", "pw")
    monkeypatch.setenv(
        "PROXIES",
        '{"http":"http://127.0.0.1:10809","https":"http://127.0.0.1:10809"}',
    )
    cfg = load_config()
    assert cfg.proxies == {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809",
    }


def test_invalid_proxies_falls_back_to_none(tmp_path, monkeypatch):
    monkeypatch.setenv("jike_email", "a@b.com")
    monkeypatch.setenv("jike_password", "pw")
    monkeypatch.setenv("PROXIES", "not-json")
    cfg = load_config()
    assert cfg.proxies is None


def test_gotify_optional(tmp_path, monkeypatch):
    monkeypatch.setenv("jike_email", "a@b.com")
    monkeypatch.setenv("jike_password", "pw")
    cfg = load_config()
    assert cfg.gotify_host is None
    assert cfg.gotify_token is None
```

- [ ] **Step 2: 跑测试确认失败**

```bash
pytest tests/test_config.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'jike_checkin.config'`。

- [ ] **Step 3: 实现 `jike_checkin/config.py`**

```python
"""配置加载：env 优先于 .env，必填校验，可选 PROXIES。"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_REQUIRED = ("jike_email", "jike_password")


class ConfigError(Exception):
    """配置错误：必填项缺失或格式非法。"""


@dataclass(frozen=True)
class Config:
    email: str
    password: str
    gotify_host: str | None
    gotify_token: str | None
    proxies: dict[str, str] | None


def _parse_proxies(raw: str | None) -> dict[str, str] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("PROXIES 解析失败，按无代理处理")
        return None
    if not isinstance(parsed, dict):
        return None
    return {str(k): str(v) for k, v in parsed.items()}


def load_config() -> Config:
    """加载并校验配置。

    优先级：进程环境变量 > .env 文件。
    必填项缺失抛 ConfigError。
    """
    load_dotenv(override=False)

    missing = [name for name in _REQUIRED if not os.environ.get(name)]
    if missing:
        raise ConfigError(f"缺少必填配置：{', '.join(missing)}")

    return Config(
        email=os.environ["jike_email"],
        password=os.environ["jike_password"],
        gotify_host=os.environ.get("gotify_host") or None,
        gotify_token=os.environ.get("gotify_token") or None,
        proxies=_parse_proxies(os.environ.get("PROXIES")),
    )
```

- [ ] **Step 4: 跑测试确认通过**

```bash
pytest tests/test_config.py -v
```

Expected: 8 passed。

- [ ] **Step 5: 提交**

```bash
git add jike_checkin/config.py tests/test_config.py
git commit -m "feat(jike_checkin): 实现配置加载模块"
```

---

## Task 3: HTTP 客户端模块

**Files:**
- Create: `jike_checkin/client.py`
- Create: `tests/test_client.py`

**Interfaces:**
- Produces:
  - `class JikeClient` — 极客云 HTTP 客户端。
  - `JikeClient(config: Config) -> None`
  - `JikeClient.login() -> bool` — 返回 `True` 当 `ret == 1`。
  - `JikeClient.checkin() -> dict` — 返回原始响应体。

- [ ] **Step 1: 写失败测试 `tests/test_client.py`**

```python
import pytest
import requests

from jike_checkin.client import JikeClient
from jike_checkin.config import Config


def _cfg(**over):
    base = dict(
        email="a@b.com",
        password="pw",
        gotify_host=None,
        gotify_token=None,
        proxies=None,
    )
    base.update(over)
    return Config(**base)


def _fake_response(json_body: dict, status_code: int = 200) -> requests.Response:
    resp = requests.Response()
    resp.status_code = status_code
    resp._content = __import__("json").dumps(json_body).encode("utf-8")
    return resp


def test_login_success(mocker):
    cfg = _cfg()
    mocker.patch.object(JikeClient, "_post", return_value=_fake_response({"ret": 1}))
    client = JikeClient(cfg)
    assert client.login() is True


def test_login_failure_returns_false(mocker):
    cfg = _cfg()
    mocker.patch.object(JikeClient, "_post", return_value=_fake_response({"ret": 0, "msg": "bad"}))
    client = JikeClient(cfg)
    assert client.login() is False


def test_login_propagates_network_error(mocker):
    cfg = _cfg()
    mocker.patch.object(
        JikeClient,
        "_post",
        side_effect=requests.RequestException("net"),
    )
    client = JikeClient(cfg)
    with pytest.raises(requests.RequestException):
        client.login()


def test_login_uses_proxies(mocker):
    cfg = _cfg(proxies={"http": "http://127.0.0.1:10809"})
    spy = mocker.patch.object(
        JikeClient, "_post", return_value=_fake_response({"ret": 1})
    )
    client = JikeClient(cfg)
    client.login()
    assert spy.call_args.kwargs.get("proxies") == cfg.proxies


def test_checkin_returns_dict(mocker):
    cfg = _cfg()
    mocker.patch.object(
        JikeClient,
        "_post",
        return_value=_fake_response({"ret": 1, "msg": "ok"}),
    )
    client = JikeClient(cfg)
    result = client.checkin()
    assert result == {"ret": 1, "msg": "ok"}


def test_checkin_sends_to_checkin_endpoint(mocker):
    cfg = _cfg()
    spy = mocker.patch.object(
        JikeClient, "_post", return_value=_fake_response({"ret": 1, "msg": "ok"})
    )
    client = JikeClient(cfg)
    client.checkin()
    url = spy.call_args.args[0]
    assert url == "https://jike138.com/user/checkin"
```

- [ ] **Step 2: 跑测试确认失败**

```bash
pytest tests/test_client.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'jike_checkin.client'`。

- [ ] **Step 3: 实现 `jike_checkin/client.py`**

```python
"""极客云 HTTP 客户端：登录与签到。"""
from __future__ import annotations

import logging
from typing import Any

import requests

from .config import Config

logger = logging.getLogger(__name__)

_LOGIN_URL = "https://jike138.com/auth/login"
_CHECKIN_URL = "https://jike138.com/user/checkin"


class JikeClient:
    """封装极客云的登录和签到 HTTP 调用。"""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._session = requests.Session()

    def _post(self, url: str, data: dict | None = None) -> requests.Response:
        kwargs: dict[str, Any] = {}
        if self._config.proxies:
            kwargs["proxies"] = self._config.proxies
        return self._session.post(url=url, data=data or {}, **kwargs)

    def login(self) -> bool:
        """登录。返回 True 当响应 ret == 1，否则 False。

        网络异常向上抛出。
        """
        response = self._post(_LOGIN_URL, data={"email": self._config.email, "passwd": self._config.password})
        result = response.json()
        return result.get("ret") == 1

    def checkin(self) -> dict:
        """签到。返回原始响应字典。

        网络异常向上抛出。
        """
        response = self._post(_CHECKIN_URL)
        return response.json()
```

- [ ] **Step 4: 跑测试确认通过**

```bash
pytest tests/test_client.py -v
```

Expected: 6 passed。

- [ ] **Step 5: 提交**

```bash
git add jike_checkin/client.py tests/test_client.py
git commit -m "feat(jike_checkin): 实现 HTTP 客户端模块"
```

---

## Task 4: Gotify 通知模块

**Files:**
- Create: `jike_checkin/notifier.py`
- Create: `tests/test_notifier.py`

**Interfaces:**
- Produces:
  - `class GotifyNotifier` — Gotify 通知。
  - `GotifyNotifier(config: Config) -> None`
  - `GotifyNotifier.send(title: str, message: str, priority: int = 0) -> None` — 失败仅记日志，不抛出。

- [ ] **Step 1: 写失败测试 `tests/test_notifier.py`**

```python
import logging

from gotify import Gotify

from jike_checkin.config import Config
from jike_checkin.notifier import GotifyNotifier


def _cfg(**over):
    base = dict(
        email="a@b.com",
        password="pw",
        gotify_host=None,
        gotify_token=None,
        proxies=None,
    )
    base.update(over)
    return Config(**base)


def test_send_noop_when_config_missing():
    notifier = GotifyNotifier(_cfg())
    notifier.send("t", "m")  # 不应抛


def test_send_calls_gotify(mocker):
    cfg = _cfg(gotify_host="https://gotify.example.com", gotify_token="tok")
    mock_client = mocker.patch.object(Gotify, "__init__", return_value=None)
    mock_create = mocker.patch.object(Gotify, "create_message")
    notifier = GotifyNotifier(cfg)
    notifier.send("hello", "world", priority=3)
    mock_client.assert_called_once_with(base_url="https://gotify.example.com", app_token="tok")
    mock_create.assert_called_once_with(title="hello", message="world", priority=3)


def test_send_swallows_exception(caplog):
    cfg = _cfg(gotify_host="https://gotify.example.com", gotify_token="tok")
    notifier = GotifyNotifier(cfg)

    def boom(*args, **kwargs):
        raise RuntimeError("network")

    notifier._client.create_message = boom  # type: ignore[attr-defined]
    with caplog.at_level(logging.ERROR, logger="jike_checkin.notifier"):
        notifier.send("t", "m")  # 不应抛
    assert any("Gotify 推送失败" in r.message for r in caplog.records)
```

- [ ] **Step 2: 跑测试确认失败**

```bash
pytest tests/test_notifier.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'jike_checkin.notifier'`。

- [ ] **Step 3: 实现 `jike_checkin/notifier.py`**

```python
"""Gotify 通知封装。失败不影响主流程。"""
from __future__ import annotations

import logging
from typing import Any

from gotify import Gotify

from .config import Config

logger = logging.getLogger(__name__)


class GotifyNotifier:
    """Gotify 通知器。配置缺失时为 no-op；推送失败仅记日志。"""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client: Gotify | None = None
        if config.gotify_host and config.gotify_token:
            self._client = Gotify(base_url=config.gotify_host, app_token=config.gotify_token)

    def send(self, title: str, message: str, priority: int = 0) -> None:
        """发送通知；配置缺失或推送失败均不抛出。"""
        if self._client is None:
            return
        try:
            self._client.create_message(title=title, message=message, priority=priority)
            logger.info("Gotify 推送成功：%s", title)
        except Exception as exc:  # noqa: BLE001 - 通知失败容错
            logger.error("Gotify 推送失败：%s", exc)
```

- [ ] **Step 4: 跑测试确认通过**

```bash
pytest tests/test_notifier.py -v
```

Expected: 3 passed。

- [ ] **Step 5: 提交**

```bash
git add jike_checkin/notifier.py tests/test_notifier.py
git commit -m "feat(jike_checkin): 实现 Gotify 通知模块"
```

---

## Task 5: 业务编排模块

**Files:**
- Create: `jike_checkin/service.py`
- Create: `tests/test_service.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class RunResult` — 含 `success: bool`、`message: str`。
  - `def run() -> RunResult` — 登录重试 ≤3 次、签到 1 次、通知触发、`ConfigError` 在内部捕获。

- [ ] **Step 1: 写失败测试 `tests/test_service.py`**

```python
import logging

import pytest
import requests

from jike_checkin.client import JikeClient
from jike_checkin.config import Config, ConfigError
from jike_checkin.notifier import GotifyNotifier
from jike_checkin.service import RunResult, run


def _cfg():
    return Config(
        email="a@b.com",
        password="pw",
        gotify_host=None,
        gotify_token=None,
        proxies=None,
    )


def test_run_success(mocker):
    cfg = _cfg()
    mocker.patch.object(JikeClient, "login", return_value=True)
    mocker.patch.object(JikeClient, "checkin", return_value={"ret": 1, "msg": "ok"})
    mock_send = mocker.patch.object(GotifyNotifier, "send")
    result = run()
    assert result == RunResult(success=True, message="ok")
    assert mock_send.call_args.kwargs["title"] == "签到成功！"


def test_run_checkin_failure(mocker):
    cfg = _cfg()
    mocker.patch.object(JikeClient, "login", return_value=True)
    mocker.patch.object(JikeClient, "checkin", return_value={"ret": 0, "msg": "already"})
    mock_send = mocker.patch.object(GotifyNotifier, "send")
    result = run()
    assert result.success is False
    assert result.message == "already"
    assert mock_send.call_args.kwargs["title"] == "签到失败"


def test_run_retries_login_three_times(mocker):
    cfg = _cfg()
    mock_login = mocker.patch.object(JikeClient, "login", return_value=False)
    mock_checkin = mocker.patch.object(JikeClient, "checkin")
    mock_send = mocker.patch.object(GotifyNotifier, "send")
    result = run()
    assert mock_login.call_count == 3
    assert mock_checkin.call_count == 0
    assert result.success is False
    assert mock_send.call_args.kwargs["title"] == "登录失败"


def test_run_login_eventual_success(mocker):
    cfg = _cfg()
    mocker.patch.object(JikeClient, "login", side_effect=[False, False, True])
    mocker.patch.object(JikeClient, "checkin", return_value={"ret": 1, "msg": "ok"})
    mock_send = mocker.patch.object(GotifyNotifier, "send")
    result = run()
    assert result.success is True
    assert mock_send.call_args.kwargs["title"] == "签到成功！"


def test_run_login_exception_retries_then_fails(mocker):
    cfg = _cfg()
    mocker.patch.object(
        JikeClient, "login", side_effect=requests.RequestException("net")
    )
    mock_checkin = mocker.patch.object(JikeClient, "checkin")
    mock_send = mocker.patch.object(GotifyNotifier, "send")
    result = run()
    assert result.success is False
    assert mock_checkin.call_count == 0
    assert mock_send.call_args.kwargs["title"] == "登录失败"


def test_run_config_error_caught(mocker):
    mocker.patch("jike_checkin.service.load_config", side_effect=ConfigError("missing jike_email"))
    result = run()
    assert result.success is False
    assert "missing jike_email" in result.message


def test_run_notifier_failure_does_not_affect_success(mocker):
    cfg = _cfg(gotify_host="https://gotify.example.com", gotify_token="tok")
    mocker.patch.object(JikeClient, "login", return_value=True)
    mocker.patch.object(JikeClient, "checkin", return_value={"ret": 1, "msg": "ok"})

    def boom(self, title, message, priority=0):
        raise RuntimeError("net")

    mocker.patch.object(GotifyNotifier, "send", new=boom)
    result = run()
    assert result.success is True
```

- [ ] **Step 2: 跑测试确认失败**

```bash
pytest tests/test_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'jike_checkin.service'`。

- [ ] **Step 3: 实现 `jike_checkin/service.py`**

```python
"""业务流程编排：登录重试、签到、通知触发。"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from .client import JikeClient
from .config import ConfigError, load_config
from .logging_setup import init_logging
from .notifier import GotifyNotifier

logger = logging.getLogger(__name__)

_LOGIN_MAX_ATTEMPTS = 3
_LOGIN_RETRY_DELAY_SECONDS = 1


@dataclass(frozen=True)
class RunResult:
    success: bool
    message: str


def _login_with_retry(client: JikeClient) -> bool:
    for attempt in range(1, _LOGIN_MAX_ATTEMPTS + 1):
        try:
            logger.info("登录尝试 %d/%d", attempt, _LOGIN_MAX_ATTEMPTS)
            if client.login():
                logger.info("登录成功")
                return True
            logger.warning("登录失败（业务返回非成功）")
        except Exception as exc:  # noqa: BLE001 - 重试兜底
            logger.warning("登录异常：%s", exc)
        if attempt < _LOGIN_MAX_ATTEMPTS:
            time.sleep(_LOGIN_RETRY_DELAY_SECONDS)
    return False


def run() -> RunResult:
    """执行一次完整签到流程。"""
    init_logging()

    try:
        config = load_config()
    except ConfigError as exc:
        logger.error("配置错误：%s", exc)
        return RunResult(success=False, message=f"配置错误：{exc}")

    client = JikeClient(config)
    notifier = GotifyNotifier(config)

    if not _login_with_retry(client):
        notifier.send(title="登录失败", message="登录失败！")
        return RunResult(success=False, message="登录失败")

    result = client.checkin()
    msg = result.get("msg", "")
    if result.get("ret") == 1:
        logger.info("签到成功：%s", msg)
        notifier.send(title="签到成功！", message=msg)
        return RunResult(success=True, message=msg)

    logger.warning("签到失败：%s", msg)
    notifier.send(title="签到失败", message=msg)
    return RunResult(success=False, message=msg)
```

- [ ] **Step 4: 跑测试确认通过**

```bash
pytest tests/test_service.py -v
```

Expected: 7 passed。

- [ ] **Step 5: 提交**

```bash
git add jike_checkin/service.py tests/test_service.py
git commit -m "feat(jike_checkin): 实现业务编排模块"
```

---

## Task 6: 根入口、配置示例与启动脚本

**Files:**
- Modify: `jikeCheckin.py`（根）
- Create: `tests/test_entry.py`
- Create: `.env.example`
- Create: `run.bat`
- Create: `run.sh`

**Interfaces:**
- Produces: `jikeCheckin.py` 入口 — 调用 `jike_checkin.service.run()` 并把 `success` 映射为退出码。

- [ ] **Step 1: 写失败测试 `tests/test_entry.py`**

```python
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_entry_exits_zero_on_success(mocker):
    mocker.patch("jike_checkin.service.run", return_value=__import__("jike_checkin.service", fromlist=["RunResult"]).RunResult(success=True, message="ok"))
    result = subprocess.run(
        [sys.executable, "jikeCheckin.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_entry_exits_nonzero_on_failure(mocker):
    mocker.patch("jike_checkin.service.run", return_value=__import__("jike_checkin.service", fromlist=["RunResult"]).RunResult(success=False, message="nope"))
    result = subprocess.run(
        [sys.executable, "jikeCheckin.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
```

- [ ] **Step 2: 跑测试确认失败**

```bash
pytest tests/test_entry.py -v
```

Expected: FAIL — 当前 `jikeCheckin.py` 还是 92 行的旧实现，子进程跑出来的是它而非 5 行入口。

- [ ] **Step 3: 替换 `jikeCheckin.py` 为 5 行入口**

写入 `jikeCheckin.py`（完整覆盖）：

```python
from jike_checkin.service import run

if __name__ == "__main__":
    raise SystemExit(0 if run().success else 1)
```

- [ ] **Step 4: 跑测试确认通过**

```bash
pytest tests/test_entry.py -v
```

Expected: 2 passed。

- [ ] **Step 5: 创建 `.env.example`**

写入 `.env.example`：

```ini
# 极客云账号（必填）
jike_email=your_email@example.com
jike_password=your_password

# Gotify 通知（可选；留空则不发送通知）
gotify_host=
gotify_token=

# HTTP 代理（可选，JSON 格式；留空则不使用代理）
# PROXIES={"http":"http://127.0.0.1:10809","https":"http://127.0.0.1:10809"}
```

- [ ] **Step 6: 创建 `run.bat`**

写入 `run.bat`：

```bat
@echo off
setlocal

if not exist ".env" (
    echo [错误] 未找到 .env 文件。请先复制 .env.example 为 .env 并填入密钥。
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 python。请先安装 Python 3.10+ 并加入 PATH。
    exit /b 1
)

python -c "import requests, gotify, dotenv" >nul 2>nul
if errorlevel 1 (
    echo [信息] 缺少依赖，正在安装 requirements.txt ...
    python -m pip install -r requirements.txt
)

python jikeCheckin.py
exit /b %ERRORLEVEL%
```

- [ ] **Step 7: 创建 `run.sh`**

写入 `run.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ".env" ]]; then
    echo "[错误] 未找到 .env 文件。请先复制 .env.example 为 .env 并填入密钥。"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "[错误] 未检测到 python3。请先安装 Python 3.10+ 并加入 PATH。"
    exit 1
fi

if ! python3 -c "import requests, gotify, dotenv" >/dev/null 2>&1; then
    echo "[信息] 缺少依赖，正在安装 requirements.txt ..."
    python3 -m pip install -r requirements.txt
fi

python3 jikeCheckin.py
```

- [ ] **Step 8: 跑全量测试确认通过**

```bash
pytest tests/ -v
```

Expected: 全部通过（约 30 个测试）。

- [ ] **Step 9: 提交**

```bash
git add jikeCheckin.py .env.example run.bat run.sh tests/test_entry.py
git commit -m "feat: 替换根入口为薄壳，添加 .env.example 与一键启动脚本"
```

---

## Task 7: 依赖与 README 收尾

**Files:**
- Modify: `requirements.txt`
- Create: `requirements-dev.txt`
- Modify: `README.md`

- [ ] **Step 1: 读现有 `requirements.txt`**

```bash
cat requirements.txt
```

Expected: 当前含 `requests`、`gotify`（可能还有其他）。

- [ ] **Step 2: 改写 `requirements.txt`**

写入 `requirements.txt`（完整覆盖，**清理 PyInstaller / pymongo / xmltodict / httpx 等历史残留**）：

```
requests>=2.28
gotify==0.5.0
python-dotenv>=1.0
```

> 决策：仅保留签到真正用到的运行时依赖。清理掉原文件中 `pyinstaller` / `pyinstall` / `pymongo` / `xmltodict` / `anyio` / `httpcore` / `httpx` / `h11` / `sniffio` / `exceptiongroup` / `pywin32-ctypes` / `pefile` / `altgraph` / `dnspython` / `certifi` / `charset-normalizer` / `idna` / `urllib3` 等无关项。`gotify` 锁回原项目使用版本 `0.5.0`（不是 `>=0.6`）。

- [ ] **Step 3: 创建 `requirements-dev.txt`**

写入 `requirements-dev.txt`：

```
-r requirements.txt
pytest>=7.0
pytest-mock>=3.10
```

- [ ] **Step 4: 验证 dev 依赖能装上**

```bash
python -m pip install -r requirements-dev.txt
pytest tests/ -v
```

Expected: 全部通过。

- [ ] **Step 5: 改写 `README.md`**

写入 `README.md`（完整覆盖）：

````markdown
# jikeCheckin

极客云签到，顺便测试 workflow。

# 使用方法

## GitHub Actions 版本

1. 点击项目右上角的 Fork，Fork 此项目。
2. 到自己 Fork 的项目点击 Setting → Secrets → New secrets。
3. Name 填写 `jike_email`，Value 填写极客网的邮箱地址。
4. 再新建 secrets，分别填上 `jike_password` 和极客网的密码。
5. 在 "Actions" 中的 "run" 下点击 "Run workflow" 即可手动执行签到。后续按 schedule 默认每天 UTC 16:30（即北京时间凌晨 00:30）自动签到，可自行修改 cron。

## 本地版本（推荐一键脚本）

### Windows

1. 克隆项目到本地。
2. 复制 `.env.example` 为 `.env`，填入 `jike_email`、`jike_password`（必填）以及 `gotify_host`、`gotify_token`（可选）。
3. 双击 `run.bat`，脚本会自动检测 Python、装依赖、跑签到。

### Linux / macOS

```bash
cp .env.example .env
# 编辑 .env 填入密钥
chmod +x run.sh
./run.sh
```

### 手动运行（高级用户）

```bash
python -m pip install -r requirements.txt
cp .env.example .env  # 编辑 .env 后执行
python jikeCheckin.py
```

# Gotify 设置

在 GitHub Action 中添加 secrets：

- `gotify_host`：`http://gotify地址`
- `gotify_token`：gotify app 密钥

本地模式同样在 `.env` 中填写这两个变量。留空则不发送通知。

# HTTP 代理

如果需要走代理，在 `.env`（或 GitHub Secrets）中设置：

```
PROXIES={"http":"http://127.0.0.1:10809","https":"http://127.0.0.1:10809"}
```

留空或格式错误则不使用代理。

# 故障排查

- 运行日志输出到控制台，并归档到 `logs/jike_checkin.log`（按天轮转，保留 7 天）。
- 退出码：0 成功 / 1 业务或配置失败。
- 常见问题：
  - 未找到 `.env`：先复制 `.env.example` 为 `.env`。
  - 依赖缺失：脚本会自动安装。如失败，手动执行 `python -m pip install -r requirements.txt`。
  - Python 版本过低：本项目要求 Python 3.10+。
````

- [ ] **Step 6: 跑全量测试最终确认**

```bash
pytest tests/ -v
```

Expected: 全部通过。

- [ ] **Step 7: 提交**

```bash
git add requirements.txt requirements-dev.txt README.md
git commit -m "docs: 更新 README 与依赖文件"
```

---

## Task 8: 端到端冒烟测试

**Files:**
- 临时本地验证用，无需新增文件。

- [ ] **Step 1: 创建临时 `.env` 验证脚本可跑通**

```bash
cp .env.example .env
# 在 .env 中填入无效的测试邮箱密码（用于触发"登录失败"通知而非真实签到）
```

- [ ] **Step 2: 在 Windows 上跑 `run.bat`**

```bash
# 在 PowerShell 中：
cmd /c run.bat
```

Expected: 看到 `[错误] 登录失败`（或类似中文输出）以及非零退出码。这是预期：测试用凭据必然登录失败。脚本本身正确即可。

- [ ] **Step 3: 在 Linux / macOS 上跑 `run.sh`（如适用）**

```bash
chmod +x run.sh
./run.sh
echo "exit code: $?"
```

Expected: 退出码非零，日志显示登录失败。

- [ ] **Step 4: 检查日志文件存在**

```bash
ls logs/
cat logs/jike_checkin.log | head -50
```

Expected: 日志文件存在，包含配置加载、登录尝试、登录失败等条目。

- [ ] **Step 5: 清理临时 `.env`**

```bash
rm .env
```

> 重要：不要把 `.env` 提交到仓库。

- [ ] **Step 6: 最终提交（如有遗漏）**

如果前面所有任务都已提交，本任务无需新提交。如果发现遗漏（例如 `.gitignore` 没把 `.env` 加进去），单独补一个提交：

```bash
echo ".env" >> .gitignore
git add .gitignore
git commit -m "chore: 忽略本地 .env 文件"
```

> 若仓库已有 `.gitignore`，先读后追加；不要覆盖已有规则。

---

## Self-Review Checklist

实施完成后，按以下顺序自查：

1. [ ] `pytest tests/ -v` 全部通过。
2. [ ] `.github/workflows/jikeWork.yml` 文件未被修改。
3. [ ] 根目录 `jikeCheckin.py` 是 5 行入口。
4. [ ] `jike_checkin/` 包内 5 个模块（`__init__`、`logging_setup`、`config`、`client`、`notifier`、`service`）齐全。
5. [ ] `.env.example`、`run.bat`、`run.sh` 存在。
6. [ ] `requirements.txt` 含 `python-dotenv`。
7. [ ] `logs/.gitkeep` 存在。
8. [ ] README 更新了本地使用方式。
9. [ ] 本地手动跑过 `run.bat` 或 `./run.sh`（Task 8 完成）。
10. [ ] `.env` 未提交到仓库。