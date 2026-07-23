# 极客云签到项目重构设计

## 概述

将现有的单文件签到脚本重构为开源友好的项目结构，支持本地运行和 GitHub Actions 自动签到。

## 目标

1. **项目结构优化**：从单文件拆分为模块化结构
2. **日志输出友好**：使用 logging 模块替代 print
3. **配置管理统一**：本地 .env + Actions Secrets，通过环境变量统一管理
4. **Actions 修复**：修正路径错误，升级依赖版本

## 项目结构

```
jikeCheckin/
├── main.py              # 入口：签到流程编排
├── config.py            # 配置：从环境变量/.env 读取
├── notify.py            # 通知：Gotify 推送
├── .env.example         # 配置模板（提交到仓库）
├── .gitignore           # 忽略 .env、__pycache__ 等
├── requirements.txt     # 精简：仅 requests + gotify + python-dotenv
├── README.md            # 重写：开源友好
└── .github/workflows/
    └── checkin.yml      # 修复路径，定时 + 手动触发
```

## 配置管理

### 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| JIKE_EMAIL | 极客云邮箱 | 是 |
| JIKE_PASSWORD | 极客云密码 | 是 |
| GOTIFY_HOST | Gotify 服务器地址 | 否 |
| GOTIFY_TOKEN | Gotify 应用 Token | 否 |
| LOG_LEVEL | 日志级别（DEBUG/INFO/WARNING/ERROR） | 否，默认 INFO |

### 本地运行

1. 复制 `.env.example` 为 `.env`
2. 填写配置项
3. 运行 `python main.py`

### GitHub Actions

在仓库 Settings → Secrets 中添加上述环境变量。

## 日志输出

使用标准 `logging` 模块，格式：

```
2024-01-15 10:30:15 [INFO] 登录成功
2024-01-15 10:30:16 [INFO] 签到成功：获得 10 积分
2024-01-15 10:30:16 [ERROR] 登录失败：密码错误
```

- INFO：正常流程（登录、签到结果）
- WARNING：已签到等可忽略情况
- ERROR：登录失败、网络错误等

## GitHub Actions 工作流

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
      - uses: actions/checkout@v4
      
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
        run: python main.py
```

## 依赖清单

```
requests>=2.31.0
gotify>=0.5.0
python-dotenv>=1.0.0
```

## 文件职责

### config.py

- 使用 `python-dotenv` 加载 `.env` 文件
- 提供 `get_config()` 函数返回配置字典
- 缺少必要配置时抛出明确错误

### notify.py

- 封装 Gotify 通知逻辑
- 提供 `send_notification(title, message)` 函数
- 未配置 Gotify 时静默跳过

### main.py

- 签到流程编排：登录 → 签到 → 通知
- 使用 logging 输出日志
- 支持重试机制（最多 3 次）

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 配置
cp .env.example .env
# 编辑 .env 填写配置

# 运行
python main.py
```

## 开源准备

- [x] 添加 `.gitignore` 忽略 `.env`
- [x] 提供 `.env.example` 模板
- [x] 重写 README.md（使用说明、配置说明）
- [x] 精简 `requirements.txt`
- [x] 修复 GitHub Actions 工作流
