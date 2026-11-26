# G-LANCE PRO — Revision 3.1.4: Python & Dependency Compatibility Report

- **Date:** 2026-11-26
- **Project:** G-LANCE PRO — Google Maps B2B Lead Extractor
- **Repository:** https://github.com/kangdidipro/google-maps-lead-extractor
- **Working Directory:** `C:\my-app\google-maps-lead-extractor`
- **Approved Baseline:** Revision 3.1.2 — Test Hardening Only
- **Author:** Google Antigravity Agent

---

## 1. Executive Summary

This report documents the targeted investigation for **Revision 3.1.4: Python & Dependency Compatibility Verification** for **G-LANCE PRO**.
The objective was to identify and verify the root cause of the compatibility discrepancy between the documented Python version (Python 3.13+) and the pinned packages in `requirements.txt` (`pandas==2.1.4`, `playwright-stealth==2.0.2`), without altering production code, documentation, requirements, or test baselines.

### Primary Findings:
1. **Actual Runtime Environment:** The workstation executes Python `3.13.5` (`C:\Python313\python.exe`) with globally installed `pandas==2.3.3` and `numpy==2.4.4`.
2. **`pandas==2.1.4` on Python 3.13 Fails to Install:** In an isolated virtual environment (`.venv_compat_test`), executing `pip install -r requirements.txt` fails with exit code `1` during metadata preparation/C-extension compilation. `pandas==2.1.4` does not provide pre-compiled wheels for Python 3.13 (which was released in October 2024, whereas pandas 2.1.4 was released in December 2023). Building from source fails due to Python 3.13 C-API changes (`_PyLong_AsByteArray` signature mismatch).
3. **`playwright-stealth` is Unused:** Static analysis confirmed that `playwright-stealth` is never imported, invoked, or referenced anywhere in the executable codebase (`main.py`, `scraper.py`, `processor.py`, `config.py`, `utils.py`, `test_regression_rev3.py`). It is an unused dependency.

---

## 2. Actual Runtime Identification

The following diagnostic commands were executed directly on the host machine:

### Commands & Results:

```bat
cmd.exe /c "where python"
```
**Output:**
```text
C:\Python313\python.exe
C:\Python310\python.exe
C:\Users\Ahadi\AppData\Local\Microsoft\WindowsApps\python.exe
```

```bat
python --version
```
**Output:** `Python 3.13.5`

```bat
python -c "import sys; print(sys.executable)"
```
**Output:** `C:\Python313\python.exe`

```bat
python -m pip --version
```
**Output:** `pip 25.2 from C:\Users\Ahadi\AppData\Roaming\Python\Python313\site-packages\pip (python 3.13)`

```bat
python -m pip show pandas
```
**Output:**
```text
Name: pandas
Version: 2.3.3
Summary: Powerful data structures for data analysis, time series, and statistics
Location: C:\Users\Ahadi\AppData\Roaming\Python\Python313\site-packages
Requires: numpy, python-dateutil, pytz, tzdata
```

```bat
python -m pip show numpy
```
**Output:**
```text
Name: numpy
Version: 2.4.4
Summary: Fundamental package for array computing in Python
Location: C:\Users\Ahadi\AppData\Roaming\Python\Python313\site-packages
```

```bat
python -m pip show playwright
```
**Output:**
```text
Name: playwright
Version: 1.63.0
Summary: A high-level API to automate web browsers
Location: C:\Users\Ahadi\AppData\Roaming\Python\Python313\site-packages
```

```bat
python -m pip show playwright-stealth
```
**Output:**
```text
WARNING: Package(s) not found: playwright-stealth
```
*(Exit code: 1)*

---

## 3. Clean Environment Installation Test

A temporary, isolated virtual environment was created outside the repository to test clean installation from `requirements.txt`:

```bat
python -m venv C:\my-app\.venv_compat_test
C:\my-app\.venv_compat_test\Scripts\python.exe -m pip install --upgrade pip
C:\my-app\.venv_compat_test\Scripts\python.exe -m pip install -r requirements.txt
```

### Result: **FAILED** (Exit code: `1`)

### Detailed Error Log:
```text
Collecting playwright==1.40.0 (from -r requirements.txt (line 1))
  Downloading playwright-1.40.0-py3-none-win_amd64.whl.metadata (3.6 kB)
Collecting playwright-stealth==2.0.2 (from -r requirements.txt (line 2))
  Using cached playwright_stealth-2.0.2-py3-none-any.whl.metadata (4.5 kB)
Collecting pandas==2.1.4 (from -r requirements.txt (line 3))
  Downloading pandas-2.1.4.tar.gz (4.3 MB)
  Installing build dependencies: finished with status 'done'
  Getting requirements to build wheel: finished with status 'done'
  Preparing metadata (pyproject.toml): finished with status 'error'
  error: subprocess-exited-with-error

  FAILED: pandas/_libs/tslibs/base.cp313-win_amd64.pyd.p/meson-generated_pandas__libs_tslibs_base.pyx.c.obj
  pandas/_libs/tslibs/base.pyx.c: error C2198: 'int _PyLong_AsByteArray(PyLongObject *,unsigned char *,size_t,int,int,int)': too few arguments for call
```

### Explanation:
- PyPI hosts pre-compiled binary wheels for `pandas==2.1.4` up to **Python 3.12**.
- No pre-built wheel exists for `cp313-win_amd64` because pandas 2.1.4 predated the release of Python 3.13.
- When `pip` falls back to building `pandas-2.1.4.tar.gz` from source on Python 3.13, Cython-generated C code invokes internal CPython APIs (`_PyLong_AsByteArray`) whose signature changed in Python 3.13, causing MSVC compiler fatal error `C2198`.

*Note: The temporary directory `C:\my-app\.venv_compat_test` was safely deleted immediately after verification.*

---

## 4. Pandas Compatibility Verification & Options

### Root Compatibility Reality:
- **`pandas==2.1.4`** officially supports **Python 3.9, 3.10, 3.11, and 3.12**. It does **not** officially support Python 3.13.
- **Python 3.13** official wheel support in pandas began with **`pandas>=2.2.3`** (which introduced pre-built wheels for Python 3.13 and updated Cython compatibility).

### Proposed Alternatives (Presented without implementation):

#### Option A: Pin Python to 3.10–3.12, Keep `pandas==2.1.4`
- **Description:** Update `README.md` to specify Python 3.10–3.12 as the required runtime rather than Python 3.13+.
- **Pros:** Preserves the exact historical pinned version `pandas==2.1.4` in `requirements.txt`.
- **Cons:** Any user running Python 3.13 (the latest standard release) will fail to install the package dependencies without a manual downgrade of their Python installation.

#### Option B: Keep Python 3.13 Support, Update `requirements.txt` to `pandas>=2.2.3` (or `pandas>=2.1.4`)
- **Description:** Adjust `requirements.txt` to permit `pandas>=2.2.3` (or range `pandas>=2.1.4,<3.0.0`), allowing modern pre-compiled wheels for Python 3.13 while remaining backwards compatible with Python 3.10–3.12.
- **Pros:**
  - Matches the host workstation's actual working environment (which already runs `pandas==2.3.3` with 19/19 passing tests).
  - Clean `pip install -r requirements.txt` succeeds instantly across Python 3.10, 3.11, 3.12, and 3.13 without requiring C++ build tools.
  - Zero code changes required (Pandas API usage in `processor.py` is simple DataFrame creation, deduplication, and `.to_excel()`, which are identical between 2.1.x and 2.2+).
- **Cons:** Changes the pinned version string in `requirements.txt`.

### Recommendation:
**Option B is the least disruptive and most robust option.** It aligns the requirements with the actual working environment and enables seamless out-of-the-box installation on modern Python 3.13 installations.

---

## 5. Playwright-Stealth Usage Audit

A comprehensive search of the codebase was conducted:

```powershell
Select-String -Path *.py -Pattern "stealth"
```
**Result:** **0 matches found.**

### Findings:
1. `playwright-stealth` is **never imported** in `main.py`, `scraper.py`, `processor.py`, `config.py`, or `utils.py`.
2. In `scraper.py`, anti-detection is currently implemented natively via custom browser context parameters:
   ```python
   context = await browser.new_context(
       user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
   )
   ```
3. On the host workstation, `python -m pip show playwright-stealth` reported `WARNING: Package(s) not found: playwright-stealth`, yet all live scraping and 19 regression tests executed with 100% success.
4. **Conclusion:** `playwright-stealth` is currently an **unused dependency** in `requirements.txt`.

---

## 6. Git Status

```text
 M README.md
 M main.py
 M processor.py
 M scraper.py
?? reports/
?? test_regression_rev3.py
?? utils.py
```

In accordance with strict verification rules:
- No production files were changed.
- No `requirements.txt` or `README.md` files were changed.
- No git staging, commit, or push was performed.
