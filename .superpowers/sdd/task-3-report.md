# Task 3 Report: 精简 requirements.txt

## Status: DONE

## Summary

Replaced the bloated `requirements.txt` (21 dependencies including pyinstaller, pymongo, httpx, xmltodict, etc.) with a minimal version containing only the 3 required dependencies.

## Changes Made

### File: `requirements.txt`

**Before (21 lines):**
```
altgraph==0.17.3
anyio==4.0.0
certifi==2023.7.22
charset-normalizer==3.2.0
dnspython==2.4.2
exceptiongroup==1.1.3
gotify==0.5.0
h11==0.14.0
httpcore==0.18.0
httpx==0.25.0
idna==3.4
pefile==2023.2.7
pyinstall==0.1.4
pyinstaller==5.13.2
pyinstaller-hooks-contrib==2023.8
pymongo==4.5.0
pywin32-ctypes==0.2.2
requests==2.31.0
sniffio==1.3.0
urllib3==2.0.5
xmltodict==0.13.0
```

**After (3 lines):**
```
requests>=2.31.0
gotify>=0.5.0
python-dotenv>=1.0.0
```

## Commits

- `d3b986e` — `chore: 精简 requirements.txt，仅保留必要依赖`

## Files Changed

- `requirements.txt` — replaced content (21 dependencies → 3 dependencies)

## Notes

- Git reports the diff as "Binary files" because the original file had encoding/line-ending differences that caused git to treat it as binary. The actual text content is correct.
- `python-dotenv` was added as a new dependency (was not in the original file) — it's needed for `.env` file loading.
- Removed unnecessary dependencies: `pyinstaller`, `pyinstall`, `pymongo`, `httpx`, `httpcore`, `xmltodict`, `dnspython`, and all their transitive sub-dependencies.
