# G-LANCE PRO — Revision 3.1.2: Test Hardening Report

- **Date:** 2026-11-26
- **Project:** G-LANCE PRO — Google Maps B2B Lead Extractor
- **Repository:** https://github.com/kangdidipro/google-maps-lead-extractor
- **Working Directory:** `C:\my-app\google-maps-lead-extractor`
- **Author:** Google Antigravity Agent

---

## 1. Executive Summary

This report documents **Revision 3.1.2: Test Hardening Only** for **G-LANCE PRO**.
The objective of this revision was to strengthen two critical automated tests in `test_regression_rev3.py` to rigorously prove:
1. **Actual DOM Replacement:** Verifying that during DOM detachment retries, `page.locator()` is invoked again and returns a distinct, newly created replacement locator instance.
2. **Same DOM, Same Business Name, Different Branch URLs:** Verifying that when multiple business branches sharing identical names exist within the same DOM, the scraper strictly and accurately selects each branch by its unique URL, never swapping branches or falling back to ambiguous name matching.

Both hardened tests execute the real production extraction function `extract_business_detail()` in `scraper.py`.
All 19 tests in the test suite pass with 100% success.

---

## 2. Test Design & Hardening Details

### Test 1 — Actual DOM Replacement (`test_production_extract_dom_replacement_retry_succeeds`)
- **Previous Limitation:** Reused a single `MockLocator` instance across retry attempts.
- **Improved Design:**
  1. Built a dynamic `locator_factory()` callable inside `MockPage`.
  2. First call to `page.locator()` returns `locator_a`.
  3. `locator_a.scroll_into_view_if_needed()` throws a simulated DOM-detachment error: `ElementHandle.scroll_into_view_if_needed: Element is not attached to the DOM`.
  4. Second call to `page.locator()` returns a completely new instance: `locator_b`.
  5. `locator_b` represents the replacement DOM element and succeeds with the extraction.
  6. **Assertions verified:**
     - `created_locators[0] is locator_a`
     - `created_locators[1] is locator_b`
     - `created_locators[0] is not created_locators[1]` (two distinct locator instances created)
     - `locator_a._attempts == 1` and `locator_b._attempts == 1`
     - Final extracted record matches expected business data.

### Test 2 — Same DOM, Same Business Name, Different Branch URLs (`test_production_extract_two_branches_correct_branch_selection_by_url`)
- **Previous Limitation:** Used separate `page1` and `page2` mock instances.
- **Improved Design:**
  1. One single `shared_page` represents a single DOM containing two distinct branch anchors:
     - `Starbucks Downtown` (`href="https://www.google.com/maps/place/Starbucks+Downtown"`)
     - `Starbucks Uptown` (`href="https://www.google.com/maps/place/Starbucks+Uptown"`)
  2. Both anchors share the identical accessible business name (`"Starbucks"`).
  3. The `shared_page` maps an ambiguous locator (`count == 2`) to the generic `aria-label="Starbucks"`.
  4. Sequentially invoked `extract_business_detail(shared_page, target_downtown)` and `extract_business_detail(shared_page, target_uptown)`.
  5. **Assertions verified:**
     - Downtown target selects the Downtown locator and extracts the Downtown URL and address.
     - Uptown target selects the Uptown locator and extracts the Uptown URL and address.
     - `loc_downtown._attempts == 1` and `loc_uptown._attempts == 1`.
     - `loc_ambiguous_name._attempts == 0` (name fallback was never called because reliable URL matching resolved the target).
     - No branch swapping or incorrect selection occurred.

---

## 3. Files Changed

1. **`test_regression_rev3.py`**:
   - Updated `MockPage` to support callable factories for dynamic per-call locator instantiation.
   - Reimplemented `test_production_extract_dom_replacement_retry_succeeds()` to verify distinct replacement locator instances.
   - Reimplemented `test_production_extract_two_branches_correct_branch_selection_by_url()` against a unified single DOM page containing multiple same-name branches.
2. **`main.py`, `scraper.py`, `processor.py`, `config.py`, `utils.py`**:
   - Preserved intact; no production modifications required.

---

## 4. Test Execution & Output

### Python Compilation Check
```bat
python -m py_compile main.py scraper.py processor.py config.py utils.py
```
*Result: Exit code 0 (clean compilation).*

### Automated Test Suite Execution
```bat
pytest test_regression_rev3.py -v
```

**Actual Terminal Output:**
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

---

## 5. Git Status

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
	reports/GLANCE-REVISION-3.1.2-TEST-HARDENING.md
	test_regression_rev3.py
	utils.py
```

No git commit or git push operations were performed.
