# G-LANCE PRO — Revision 3.1: Selector & Locator Hardening Report

- **Date:** 2026-11-26
- **Project:** G-LANCE PRO — Google Maps B2B Lead Extractor
- **Repository:** https://github.com/kangdidipro/google-maps-lead-extractor
- **Working Directory:** `C:\my-app\google-maps-lead-extractor`
- **Author:** Google Antigravity Agent

---

## 1. Executive Summary

This report documents **Revision 3.1: Selector & Locator Hardening** for **G-LANCE PRO**.
Building directly upon the architecture introduced in Revision 3, this engineering stabilization addresses three core improvements:
1. **Safe & Conservative URL Normalization:** Replaced crude string stripping and unconditional lowercasing with standards-compliant Python `urllib.parse` utilities, preserving case-sensitive paths, removing only known tracking parameters (`authuser`, `hl`, `gl`, `g_ep`, `utm_*`), and retaining unknown/store-identifying query parameters.
2. **Safe Playwright Locator Construction:** Eliminated unsafe CSS string interpolation. Integrated Playwright Locator filtering (`locator.filter()`), CSS value escaping (`css_escape()`), and accessible role matching (`get_by_role()`) to handle business names with quotes, apostrophes, ampersands, and unicode characters safely.
3. **Genuine Automated Tests for Production Extraction Logic:** Refactored per-business extraction into a standalone production function `extract_business_detail()` in `scraper.py`. Replaced mock tests that simulated their own internal retry loops with genuine tests that directly invoke `extract_business_detail()`.

---

## 2. Problems Addressed

| Area | Prior Weakness (Revision 3) | Implemented Hardening (Revision 3.1) |
| :--- | :--- | :--- |
| **URL Normalization** | Entire URL was lowercased (`u.lower()`) and query strings were stripped unconditionally (`u.split("?")[0]`), risking mutation of case-sensitive path IDs or loss of store-specific query parameters. | `urllib.parse` used: scheme and hostname normalized to lowercase; path case strictly preserved; fragments stripped; only explicit tracking parameters removed; unknown parameters preserved in sorted order. |
| **Locator Construction** | Used raw f-string interpolation: `page.locator(f'a.hfpxzc[href="{raw_href}"]')`. Unescaped quotes or apostrophes in names/URLs could break selector parsing. | Constructed locators via `locator('a.hfpxzc').filter(...)` with safe `css_escape()` escaping, plus exact `get_by_role("link", ...)` fallback. |
| **Automated Testing** | Tests in `test_regression_rev3.py` re-implemented their own retry loops rather than executing the scraper's code. | Production extraction decoupled into `extract_business_detail()`. Tests directly invoke this production function against mocked Playwright boundaries. |

---

## 3. Files Changed

### 1. `utils.py`
- Rewrote `normalize_url(url)` using standard library `urllib.parse` (`urlparse`, `parse_qsl`, `urlencode`, `urlunparse`).
- Scheme and netloc/hostname are converted to lowercase.
- URL path case is preserved intact; trailing slashes are cleanly stripped.
- Query parameters are parsed; only items matching `KNOWN_TRACKING_PARAMS` (or starting with `utm_`) are filtered out.
- Unknown query parameters are preserved in canonical sorted order.
- URL fragments are removed.
- Malformed inputs are handled gracefully without raising exceptions.

### 2. `scraper.py`
- Added `css_escape(val)` utility to escape quotes (`"`) and backslashes (`\`) in attribute selectors.
- Factored out per-business extraction into:
  ```python
  async def extract_business_detail(page, target, index=1, total_targets=1, max_retries=3, feed_locator=None)
  ```
- Locator lookup sequentially attempts:
  1. Safe filter matching exact raw `href`.
  2. Safe filter matching base path prefix.
  3. Safe filter matching exact `aria-label`.
  4. Accessible role matching via `page.get_by_role("link", name=target_name, exact=True)`.
- Main orchestrator `get_google_maps_data()` calls `extract_business_detail()` directly, maintaining clean separation of concerns.

### 3. `test_regression_rev3.py`
- Completely overhauled test suite to 18 unit and integration tests across 4 dedicated sections:
  - **Part 1:** Safe URL Normalization Tests (8 tests covering hostname casing, path case preservation, tracking removal, unknown param preservation, fragment removal, trailing slashes, malformed inputs, duplicate matching).
  - **Part 2:** Safe Locator & CSS Escape Tests (special characters, quotes, apostrophes).
  - **Part 3:** Genuine Production Extraction Tests calling `extract_business_detail()` directly (success on attempt 1, simulated DOM detachment with attempt 2 success, retry exhaustion, special characters, distinct branch URLs).
  - **Part 4:** Processor and Excel Deduplication Tests.

---

## 4. Test Execution & Verification

### Compilation Verification
```bat
python -m py_compile main.py scraper.py processor.py config.py utils.py
```
*Result: Clean compilation (exit code 0).*

### Automated Test Suite Execution
```bat
pytest test_regression_rev3.py -v
```

**Actual Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0 -- C:\Python313\python.exe
cachedir: .pytest_cache
rootdir: C:\my-app\google-maps-lead-extractor
plugins: anyio-4.15.1, hydra-core-1.3.2, langsmith-0.14.12
collecting ... collected 18 items

test_regression_rev3.py::test_url_normalization_hostname_case PASSED     [  5%]
test_regression_rev3.py::test_url_normalization_path_case_preserved PASSED [ 11%]
test_regression_rev3.py::test_url_normalization_known_tracking_params_removed PASSED [ 16%]
test_regression_rev3.py::test_url_normalization_unknown_query_params_preserved PASSED [ 22%]
test_regression_rev3.py::test_url_normalization_fragment_removed PASSED  [ 27%]
test_regression_rev3.py::test_url_normalization_trailing_slash_handling PASSED [ 33%]
test_regression_rev3.py::test_url_normalization_empty_and_malformed PASSED [ 38%]
test_regression_rev3.py::test_url_normalization_duplicate_detection PASSED [ 44%]
test_regression_rev3.py::test_css_escape_special_characters PASSED       [ 50%]
test_regression_rev3.py::test_production_extract_success_first_attempt PASSED [ 55%]
test_regression_rev3.py::test_production_extract_dom_detachment_retry_succeeds PASSED [ 61%]
test_regression_rev3.py::test_production_extract_retry_exhaustion_returns_none PASSED [ 66%]
test_regression_rev3.py::test_production_extract_special_characters_in_name_and_url PASSED [ 72%]
test_regression_rev3.py::test_production_extract_different_branch_urls_assigned PASSED [ 77%]
test_regression_rev3.py::test_dedup_duplicate_urls_different_params PASSED [ 83%]
test_regression_rev3.py::test_dedup_different_branches_same_name PASSED  [ 88%]
test_regression_rev3.py::test_insufficient_identity_records_preserved PASSED [ 94%]
test_regression_rev3.py::test_excel_export_schema_and_counts PASSED      [100%]

============================= 18 passed in 1.57s ==============================
```

### Live Smoke Test (Separate from Mocked Tests)
```bat
python main.py "Coffee Shop Jakarta" --limit 5 --scrolls 2 --headless
```

**Live Output:**
- Discovered listings: 12
- Unique selected targets: 5
- Successfully extracted: **5/5 (100% success rate)**
- Failures: **0**
- File generated: `GLANCE_Coffee_Shop_Jakarta_20261126_142424.xlsx`
- Export row count matched extracted records exactly.

---

## 5. Exact Windows Commands for Manual UAT

To manually verify the live scraper on Windows workstations:

### 1. Default Visual UAT (Standard Headful Browser)
```bat
python main.py "Coffee Shop Jakarta" --limit 10 --scrolls 5
```

### 2. High-Volume Headless UAT
```bat
python main.py "Restaurant Jakarta" --limit 20 --scrolls 8 --headless
```

### 3. Special Characters & Path Encoding UAT
```bat
python main.py "Cafe/Restaurant Jakarta" --limit 5 --headless
```

### 4. Run Automated Test Suite
```bat
pytest test_regression_rev3.py -v
```

---

## 6. Known Limitations

1. **Google Maps DOM Rate Limiting & Bot Detection:** Running large batch runs (e.g., hundreds of leads) in rapid succession without proxy rotation may trigger Google bot challenges or localized search throttling.
2. **Viewport Listing Cap:** Google Maps web interface limits initial feed results to around 60–120 businesses per geographical viewport without panning or zooming the map.
3. **Dynamic CSS Selectors:** Google Maps periodically updates internal class hashes (e.g. `a.hfpxzc`, `button[data-item-id="address"]`). If Google alters these attributes, selectors will need updating.

---

## 7. Git Status

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
	modified:   README.md
	modified:   main.py
	modified:   processor.py
	modified:   scraper.py

Untracked files:
	reports/GLANCE-CLI-ENHANCEMENT.md
	reports/GLANCE-REVISION-3-DOM-RELIABILITY.md
	reports/GLANCE-REVISION-3.1-SELECTOR-HARDENING.md
	test_regression_rev3.py
	utils.py
```

No git commit or git push operations were performed.
