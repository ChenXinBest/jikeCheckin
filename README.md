# 极客云签到

自动签到极客云，支持本地运行和 GitHub Actions 定时执行。

## 功能特性

- ✅ 自动登录签到
- ✅ 支持 Gotify 通知
- ✅ 支持 WXPUSH 通知（微信推送）
- ✅ 多渠道通知：配置完整的渠道都会收到
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
     - `WXPUSH_BASE_URL`：WXPUSH 推送地址（可选，使用该渠道时必填）
     - `WXPUSH_USERID`：WXPUSH 用户 ID（可选）
     - `WXPUSH_TEMPLATE_ID`：WXPUSH 模板 ID（可选）

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
| WXPUSH_BASE_URL | WXPUSH 推送地址（使用该渠道时必填） | 否 | - |
| WXPUSH_USERID | WXPUSH 用户 ID | 否 | - |
| WXPUSH_TEMPLATE_ID | WXPUSH 模板 ID | 否 | - |
| JIKE_PROXY | 代理地址，如 `http://127.0.0.1:7890`（直连失败时才需要） | 否 | 直连 |
| LOG_LEVEL | 日志级别（DEBUG/INFO/WARNING/ERROR） | 否 | INFO |

> 提示：站点对非浏览器请求会返回 `403 Forbidden`，脚本使用 [fake-useragent](https://pypi.org/project/fake-useragent/) 随机生成真实的桌面端 User-Agent（依赖已写入 `requirements.txt`）；
> 若日志中出现 403，可尝试配置 `JIKE_PROXY` 或标准 `HTTPS_PROXY` 环境变量。

## 通知渠道

程序支持两个通知渠道，**配置完整的渠道都会收到消息**，互不影响：

| 渠道 | 需要的配置 | 标题 | 内容 |
|------|-----------|------|------|
| Gotify | `GOTIFY_HOST` + `GOTIFY_TOKEN` | 签到成功 / 签到失败 | 站点返回的签到消息 |
| WXPUSH | `WXPUSH_BASE_URL` + `WXPUSH_USERID` + `WXPUSH_TEMPLATE_ID` | `✓成功` / `×失败` | `获得流量：666MB；执行用时：12s` |

WXPUSH 说明：

- 推送地址、用户 ID、模板 ID 全部通过环境变量传入（本地放 `.env`，GitHub Actions 放 Secrets），仓库内不存放真实值与真实域名；
- 标题固定为 `✓成功`（签到成功）或 `×失败`（登录/签到失败）；
- 内容格式为 `获得流量：{流量+单位}；执行用时：{脚本执行用时+单位}`；
- 流量优先从签到消息中解析，解析不到时回退到账户面板的流量信息；实在拿不到则按 `0MB` 展示。

> 提示：日志中不会打印 `userid` / `template_id` / 推送域名，避免在 CI 日志里泄露。

## 日志输出示例

```
2024-01-15 10:30:15 [INFO] 极客云签到开始
2024-01-15 10:30:15 [INFO] 第 1/3 次尝试
2024-01-15 10:30:15 [INFO] 正在登录...
2024-01-15 10:30:16 [INFO] 登录成功，正在签到...
2024-01-15 10:30:17 [INFO] 签到成功：获得 10 积分
2024-01-15 10:30:17 [INFO] 获得流量：666MB
2024-01-15 10:30:17 [INFO] WXPUSH 通知发送成功：{"code":0}
2024-01-15 10:30:17 [INFO] 通知发送成功：wxpush
2024-01-15 10:30:17 [INFO] 签到完成
```

## 项目结构

```
jikeCheckin/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── notify.py            # 通知模块（Gotify / WXPUSH）
├── traffic.py           # 流量解析工具
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

### Q: 如何禁用 WXPUSH 通知？

不配置 `WXPUSH_BASE_URL` / `WXPUSH_USERID` / `WXPUSH_TEMPLATE_ID` 即可，程序会自动跳过通知。
两个渠道互不影响，只配置其中一个也可以。

### Q: 签到失败怎么办？

1. 检查账号密码是否正确
2. 检查网络是否正常
3. 查看日志输出，定位具体错误
4. 程序会自动重试最多 3 次

## License

MIT
