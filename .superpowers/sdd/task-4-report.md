# Task 4 Report: 创建 config.py 配置模块

## Status: DONE

## Commits Created
- `a955c2e` feat: 添加配置管理模块 config.py

## Files Changed
- Created: `config.py` (34 lines)

## Summary
Created `config.py` with `get_config()` function that:
- Loads environment variables from `.env` via `python-dotenv`
- Validates required `JIKE_EMAIL` and `JIKE_PASSWORD` (exits with error if missing)
- Returns config dict with: `jike_email`, `jike_password`, `gotify_host`, `gotify_token`, `log_level`
- Defaults `log_level` to `"INFO"` if not set

Code matches the brief exactly. Committed with the specified message.
