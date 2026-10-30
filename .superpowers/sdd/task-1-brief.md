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
