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
