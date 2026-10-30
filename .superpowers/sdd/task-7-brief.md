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
