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
