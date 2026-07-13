# 极客云签到项目重构与本地运行支持 — 设计

- **日期**：2026-07-13
- **状态**：草案，待用户审批
- **范围**：在保证原功能与 GitHub Action 不改变的前提下，重构代码结构并支持 Windows / Linux 一键本地运行

## 1. 背景与目标

项目 `jikeCheckin` 已经稳定运行多年。现有痛点：

1. 全部逻辑堆在单文件 `jikeCheckin.py`（92 行），结构混乱：全局变量读取配置、类内嵌读取全局变量、错误处理粗糙。
2. README 提示本地用户**改源码**填邮箱密码（`os.environ.get("jike_email")` 改成字面量），既不优雅也不安全。
3. 没有 Windows / Linux 启动脚本。用户首次运行需要手动 `pip install`、手动管理 `.env`、手动运行。
4. 没有日志归档，跑完一次只看到当时控制台输出，出问题难以复盘。
5. 重试逻辑放在 `__main__`，含义隐晦；异常未捕获，网络抖动直接崩。

**目标**：

- 拆分为职责清晰的模块，每个文件 ≤50 行。
- 本地用户复制 `.env.example` → 填密钥 → 双击 `run.bat` 或 `./run.sh` 即可运行。
- 保留 GitHub Action 行为不变（`.github/workflows/jikeWork.yml` 不动）。
- 引入结构化日志（控制台 + 文件归档）。
- 修复隐晦的重试逻辑，明确边界。

## 2. 设计原则

- **不破坏既有行为**：原 `ret == 1` 即成功的判定、Gotify 通知字段、登录失败重试 ≤3 次的语义都要保留。
- **Action 不动**：`.github/workflows/jikeWork.yml` 一字不改；入口仍是根目录 `jikeCheckin.py`。
- **依赖最少**：仅引入 `python-dotenv`（配置加载）；测试用 `pytest` + `pytest-mock`（开发依赖）。
- **小而清晰**：每个模块单一职责，对外接口最小化。

## 3. 目录结构

```
jikeCheckin/                              # 仓库根
├── jikeCheckin.py                        # 薄入口（保留，~5 行）
├── jike_checkin/                         # 主包
│   ├── __init__.py
│   ├── config.py                         # 配置加载
│   ├── client.py                         # 极客云 HTTP 客户端
│   ├── notifier.py                       # Gotify 通知
│   └── service.py                        # 业务流程编排
├── tests/                                # 单元测试
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_client.py
│   ├── test_notifier.py
│   └── test_service.py
├── logs/                                 # 日志目录（运行时生成，.gitkeep 占位）
│   └── .gitkeep
├── .env.example                          # 配置示例（提交到仓库）
├── requirements.txt                      # 运行时依赖
├── requirements-dev.txt                  # 开发依赖
├── run.bat                               # Windows 启动脚本
├── run.sh                                # Linux / macOS 启动脚本
├── README.md                             # 更新使用文档
└── .github/workflows/jikeWork.yml        # 不动
```

## 4. 模块设计

### 4.1 `jike_checkin/config.py` — 配置加载

**职责**：从 `.env` 和环境变量合并加载配置，校验必填项。

**关键规则**：

- `python-dotenv.load_dotenv()`：默认 `override=False`，环境变量优先于 `.env`。
- 必填：`jike_email`、`jike_password`。缺失则 `raise ConfigError("缺少必填配置：xxx")`。
- 可选：`gotify_host`、`gotify_token`、`PROXIES`。
- `PROXIES` 是 JSON 字符串，例如 `{"http":"http://127.0.0.1:10809","https":"http://127.0.0.1:10809"}`；解析失败则忽略并按无代理处理。
- 配置值**不写入日志**，仅记录字段名。

**对外接口**：

```python
@dataclass(frozen=True)
class Config:
    email: str
    password: str
    gotify_host: str | None
    gotify_token: str | None
    proxies: dict[str, str] | None

def load_config() -> Config: ...
```

### 4.2 `jike_checkin/client.py` — 极客云 HTTP 客户端

**职责**：封装极客云的登录和签到 HTTP 调用，对外暴露业务方法。

**行为契约**：

- `JikeClient(config).login()` 返回 `bool`：`True` 表示 `ret == 1`。
- `JikeClient(config).checkin()` 返回 `dict`：原始响应体，由调用方解读 `ret`。
- 网络异常（`requests.RequestException`）**向上抛出**，不吞。
- HTTP 非 200 视为异常，向上抛出。
- JSON 解析失败向上抛出。
- Proxies 通过 `requests.Session.get/post` 的 `proxies` 参数传入；空则不传。

**对外接口**：

```python
class JikeClient:
    def __init__(self, config: Config) -> None: ...
    def login(self) -> bool: ...
    def checkin(self) -> dict: ...
```

### 4.3 `jike_checkin/notifier.py` — Gotify 通知

**职责**：发送 Gotify 通知。失败不影响主流程。

**行为契约**：

- `GotifyNotifier(config).send(title, message, priority=0)` 在 `gotify_host` 和 `gotify_token` 都存在时才有效；否则为 no-op。
- 通知失败（异常）只记录 ERROR 日志，不向上抛出。
- `priority` 默认 0（与原行为一致）。

**对外接口**：

```python
class GotifyNotifier:
    def __init__(self, config: Config) -> None: ...
    def send(self, title: str, message: str, priority: int = 0) -> None: ...
```

### 4.4 `jike_checkin/service.py` — 业务流程编排

**职责**：把 client 和 notifier 组装为完整业务流程。

**业务规则**：

1. 登录：最多重试 3 次，每次间隔 1 秒。任一次成功则继续；3 次都失败则发"登录失败"通知并返回退出码非零。
2. 签到：仅 1 次。成功发"签到成功"通知；失败（`ret != 1`）发"签到失败"通知。
3. Gotify 推送失败**不重试**，仅日志 ERROR，不影响退出码判定。
4. 返回 `RunResult(success: bool, message: str)`；`message` 包含人类可读原因。
5. 退出码：成功 0，业务失败 1，配置错误 2。

**对外接口**：

```python
@dataclass(frozen=True)
class RunResult:
    success: bool
    message: str

def run() -> RunResult: ...
```

### 4.5 `jikeCheckin.py`（根） — 入口

```python
from jike_checkin.service import run

if __name__ == "__main__":
    raise SystemExit(0 if run().success else 1)
```

仅 5 行。`SystemExit` 让 GitHub Action 能拿到非零退出码。

## 5. 配置加载与优先级

**优先级**（从高到低）：

1. 进程已有的环境变量（Action 模式天然满足）
2. `.env` 文件中的键（本地模式）
3. `.env` 不存在 → 本地启动脚本检测后提示退出；Action 模式则继续走纯环境变量路径

**`.env.example` 内容**：

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

## 6. 启动脚本设计

### 6.1 `run.bat`（Windows 原生 cmd）

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

### 6.2 `run.sh`（Linux / macOS bash）

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

### 6.3 设计要点

- 不创建虚拟环境（保持简单）。
- 不修改 `.env` 内容（用户的密钥原样保留）。
- 两个脚本逻辑保持一致（先检查 `.env` → 检 Python → 装依赖 → 跑）。
- Windows 用 `cmd` 原生语法，**不依赖 PowerShell**，兼容性最好。
- 退出码透传：业务失败时退出码非零，方便 CI / 任务计划器判断。

## 7. 日志方案

- 日志器名：`jike_checkin`（包级）。
- 格式：`%(asctime)s | %(levelname)-7s | %(name)s | %(message)s`。
- 控制台 handler：INFO 及以上。
- 文件 handler：`logs/jike_checkin.log`，DEBUG 及以上，按天轮转，保留 7 份。
- 日志目录 `logs/` 由代码自动创建；仓库保留 `logs/.gitkeep` 占位。
- 初始化时机：`service.run()` 入口处调用 `_init_logging()` 一次。

**关键日志点**（不含敏感值）：

| 事件 | 级别 |
|---|---|
| 配置加载完成（仅字段名） | INFO |
| 登录尝试开始 / 成功 / 失败 | INFO / INFO / WARNING |
| 签到成功 / 业务失败 | INFO / WARNING |
| Gotify 推送成功 / 失败 | INFO / ERROR |
| 配置缺失 / 网络异常 | ERROR |

## 8. 错误处理总览

| 场景 | 行为 |
|---|---|
| `.env` 不存在（本地） | 启动脚本检测后退出码 1 |
| 必填配置缺失 | `ConfigError` 异常，日志 ERROR，退出码 2 |
| 网络异常（登录） | service 层捕获，重试 ≤3 次 |
| 网络异常（签到） | service 层捕获，业务失败，退出码 1 |
| HTTP 非 200 | 同上，抛出 → 重试或失败 |
| API 返回 `ret != 1` | 业务失败，发通知，退出码 1 |
| Gotify 推送失败 | 仅日志 ERROR，不影响退出码 |
| JSON 解析失败 | 客户端层抛出，service 层捕获并记 ERROR |

## 9. 测试策略

**测试框架**：`pytest` + `pytest-mock`（开发依赖，写入 `requirements-dev.txt`）。

**测试用例**：

| 文件 | 覆盖 |
|---|---|
| `test_config.py` | env 优先于 `.env`、必填校验缺失、PROXIES 解析失败容错 |
| `test_client.py` | mock `requests.Session`：login 成功 / 失败（ret != 1）/ 网络异常 / proxies 传入 |
| `test_notifier.py` | mock gotify client：send 调用参数正确；缺配置时为 no-op；通知失败不抛 |
| `test_service.py` | mock client + notifier：登录 3 次重试、签到不重试、通知触发条件、退出码 |

**不测**：

- `jikeCheckin.py`（仅 5 行入口）
- `run.bat` / `run.sh`（脚本由启动脚本独立的人工测试覆盖）

**覆盖率**：不引入 coverage 工具（YAGNI）。

## 10. 依赖

**`requirements.txt`**：

```
requests>=2.28
gotify>=0.6
python-dotenv>=1.0
```

**`requirements-dev.txt`**：

```
-r requirements.txt
pytest>=7.0
pytest-mock>=3.10
```

**Action 兼容性**：

Action 现有 step 是 `pip3 install -r requirements.txt`，新依赖 `python-dotenv` 会被一并安装，无需改 Action。

## 11. README 更新要点

- 本地版从"改源码"改成"复制 `.env.example` 到 `.env` → 填密钥 → 双击 `run.bat` / `./run.sh`"。
- 删掉 README 中"将下述代码注释"的旧段落。
- 新增"故障排查"：日志在 `logs/jike_checkin.log`，退出码含义（0 成功 / 1 业务失败 / 2 配置错误）。
- GitHub Action 段不变。

## 12. 不在范围内（YAGNI）

- 多种通知渠道（Bark、邮件、Server 酱）—— 当前只有 Gotify 需求。
- 拆 `client.py` 为 HTTP 层 + endpoint 层 —— 只有 2 个端点。
- 拆 `notifier.py` 为接口 + 实现 —— 同上。
- 打包成 exe（PyInstaller）。
- 创建虚拟环境 / Poetry / uv —— 保持 `pip + requirements.txt` 现状。
- CI 测试 workflow —— 用户没要求，且不影响 Action 签到行为。
- 国际化（i18n）—— 项目本身就是中文环境。
- 覆盖率工具 —— YAGNI。

## 13. 迁移步骤概要

1. 创建 `jike_checkin/` 包及 4 个模块文件。
2. 创建 `tests/` 目录及 4 个测试文件。
3. 把根目录 `jikeCheckin.py` 替换为薄入口。
4. 新增 `.env.example`、`run.bat`、`run.sh`。
5. 更新 `requirements.txt`、新增 `requirements-dev.txt`。
6. 新增 `logs/.gitkeep`。
7. 更新 `README.md`。
8. 运行 `pytest` 全绿。
9. 本地手动跑一次 `run.bat` 或 `./run.sh` 验证。

GitHub Action 流程（`.github/workflows/jikeWork.yml`）一字不改。