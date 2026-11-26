# G-LANCE PRO — Revision 3.1.1: Locator Matching Correction Report

- **Date:** 2026-11-26
- **Project:** G-LANCE PRO — Google Maps B2B Lead Extractor
- **Repository:** https://github.com/kangdidipro/google-maps-lead-extractor
- **Working Directory:** `C:\my-app\google-maps-lead-extractor`
- **Author:** Google Antigravity Agent

---

## 1. Executive Summary

This report documents **Revision 3.1.1: Locator Matching Correction** for **G-LANCE PRO**.
Independent review of Revision 3.1 identified an engineering defect in the locator matching strategy:
```python
all_cards = page.locator('a.hfpxzc')
loc_exact = all_cards.filter(has=page.locator(f'[href="{css_escape(raw_href)}"]'))
```
In Playwright, `locator.filter(has=...)` searches for **descendants** of the matching element. However, the attributes `href` and `aria-label` belong directly to the anchor element (`a.hfpxzc`) itself, not to any of its children. This could lead to matching failures or unintended selector misbehavior.

Revision 3.1.1 resolves this issue by switching to direct anchor attribute matching with proper CSS escaping and implementing strict ambiguity guards for same-name branches.

---

## 2. Issues Corrected

1. **Direct Anchor Attribute Matching:**
   - Replaced descendant-based `.filter(has=...)` with direct attribute selectors on the target anchor element:
     ```python
     loc_exact = page.locator(f'a.hfpxzc[href="{css_escape(raw_href)}"]')
     loc_base = page.locator(f'a.hfpxzc[href^="{css_escape(base_path)}"]')
     loc_aria = page.locator(f'a.hfpxzc[aria-label="{css_escape(target_name)}"]')
     ```
   - Values are safely escaped using `css_escape()`, avoiding raw unescaped interpolation while directly targeting the anchor's own attributes.

2. **Branch Ambiguity Protection:**
   - If URL matching is unavailable and the scraper must fall back to business name matching, the locator strictly checks the match count:
     - `count == 1`: Selected safely.
     - `count > 1`: Multiple branches exist with the identical name. Rather than silently selecting the first element (which could select the wrong branch), it raises an explicit ambiguity exception:
       `RuntimeError: Ambiguous target: N branches found with name '...' but URL identity cannot be verified.`
     - This guarantees that branch identity is never falsely swapped or corrupted.

3. **Preserved Architecture & Bounded Retries:**
   - Retained bounded retry behavior (3 attempts) with exponential human-like delays and micro-scroll DOM recovery.
   - Preserved normalized URL matching as the primary business identity strategy.
   - Maintained clean separation of concerns: production per-business extraction in `extract_business_detail()`.

---

## 3. Files Modified

1. **`scraper.py`**:
   - Updated `extract_business_detail()` to use direct anchor attribute matching (`a.hfpxzc[href="..."]`, `a.hfpxzc[href^="..."]`, and `a.hfpxzc[aria-label="..."]`).
   - Added branch ambiguity verification (`aria_count > 1` and `role_count > 1`) preventing silent mis-selection of same-name branches.

2. **`test_regression_rev3.py`**:
   - Expanded to 19 comprehensive tests calling production `extract_business_detail()` directly:
     - Exact anchor `href` matching.
     - DOM replacement & retry recovery.
     - Business names containing quotes, apostrophes, ampersands, and brackets.
     - Correct branch selection by distinct URLs when names are identical.
     - Ambiguous name fallback guard: verifying that multiple same-name branches without URL fail safely rather than selecting the wrong branch.
     - Retry exhaustion handling.
     - URL normalization and processor Excel export tests.

---

## 4. Test Execution & Verification

### Python Compilation Check
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
collecting ... collected 19 items

test_regression_rev3.py::test_url_normalization_hostname_case PASSED     [  5%]
test_regression_rev3.py::test_url_normalization_path_case_preserved PASSED [ 10%]
test_regression_rev3.py::test_url_normalization_known_tracking_params_removed PASSED [ 15%]
test_regression_rev3.py::test_url_normalization_unknown_query_params_preserved PASSED [ 21%]
test_regression_rev3.py::test_url_normalization_fragment_removed PASSED  [ 26%]
test_regression_rev3.py::test_url_normalization_trailing_slash_handling PASSED [ 31%]
test_regression_rev3.py::test_url_normalization_empty_and_malformed PASSED [ 36%]
test_regression_rev3.py::test_url_normalization_duplicate_detection PASSED [ 42%]
test_regression_rev3.py::test_css_escape_special_characters PASSED       [ 47%]
test_regression_rev3.py::test_production_extract_exact_anchor_href_matching PASSED [ 52%]
test_regression_rev3.py::test_production_extract_dom_replacement_retry_succeeds PASSED [ 57%]
test_regression_rev3.py::test_production_extract_special_characters_escaping PASSED [ 63%]
test_regression_rev3.py::test_production_extract_two_branches_correct_branch_selection_by_url PASSED [ 68%]
test_regression_rev3.py::test_production_extract_ambiguous_name_fallback_fails_safely PASSED [ 73%]
test_regression_rev3.py::test_production_extract_retry_exhaustion_returns_none PASSED [ 78%]
test_regression_rev3.py::test_dedup_duplicate_urls_different_params PASSED [ 84%]
test_regression_rev3.py::test_dedup_different_branches_same_name PASSED  [ 89%]
test_regression_rev3.py::test_insufficient_identity_records_preserved PASSED [ 94%]
test_regression_rev3.py::test_excel_export_schema_and_counts PASSED      [100%]

============================= 19 passed in 1.27s ==============================
```

### Live Smoke Test Verification (Separate from Mock Tests)
```bat
python main.py "Coffee Shop Jakarta" --limit 5 --scrolls 2 --headless
```

**Live Results:**
- Total discovered: 12
- Unique selected targets: 5
- Successfully extracted: **5/5 (100%)**
- Failures: **0**
- File saved: `GLANCE_Coffee_Shop_Jakarta_20261126_142914.xlsx` (5 records).

---

## 5. Exact Windows Commands for Manual UAT

```bat
:: 1. UAT Visual Browser (Standard Headful)
python main.py "Coffee Shop Jakarta" --limit 10 --scrolls 5

:: 2. UAT Volume Lebih Tinggi (Headless)
python main.py "Restaurant Jakarta" --limit 20 --scrolls 8 --headless

:: 3. UAT Keyword Karakter Khusus & Slashes
python main.py "Cafe/Restaurant Jakarta" --limit 5 --headless

:: 4. Menjalankan Seluruh Suite Tes Regresi Otomatis
pytest test_regression_rev3.py -v
```

---

## 6. Git Status

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
	reports/GLANCE-REVISION-3.1.1-LOCATOR-CORRECTION.md
	test_regression_rev3.py
	utils.py
```

No git commit or git push operations were performed.
