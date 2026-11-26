import asyncio
import pytest
import pandas as pd
from utils import normalize_url, normalize_text
from processor import save_data
from scraper import extract_business_detail, css_escape

# =====================================================================
# PART 1: Safe URL Normalization Tests (Requirement A)
# =====================================================================

def test_url_normalization_hostname_case():
    """Scheme and hostname must be normalized to lowercase."""
    url = "HTTPS://WWW.Google.COM/maps/place/SomePlace"
    assert normalize_url(url) == "https://www.google.com/maps/place/SomePlace"

def test_url_normalization_path_case_preserved():
    """Path casing must be strictly preserved."""
    url = "https://maps.google.com/maps/place/CaseSensitive_ID123/Details"
    assert normalize_url(url) == "https://maps.google.com/maps/place/CaseSensitive_ID123/Details"

def test_url_normalization_known_tracking_params_removed():
    """Known tracking parameters like authuser, hl, gl, g_ep, utm_* must be removed."""
    url = "https://maps.google.com/place/Cafe?authuser=0&hl=id&gl=id&utm_source=feed&utm_campaign=winter"
    assert normalize_url(url) == "https://maps.google.com/place/Cafe"

def test_url_normalization_unknown_query_params_preserved():
    """Unknown or identifying query parameters must be preserved."""
    url = "https://maps.google.com/place/Branch?store_id=987&custom_param=xyz&authuser=0"
    norm = normalize_url(url)
    assert "store_id=987" in norm
    assert "custom_param=xyz" in norm
    assert "authuser=0" not in norm

def test_url_normalization_fragment_removed():
    """URL fragments (#) must be stripped."""
    url = "https://maps.google.com/place/Cafe#review-section"
    assert normalize_url(url) == "https://maps.google.com/place/Cafe"

def test_url_normalization_trailing_slash_handling():
    """Trailing slashes must be stripped from paths."""
    url = "https://maps.google.com/place/Cafe/"
    assert normalize_url(url) == "https://maps.google.com/place/Cafe"

def test_url_normalization_empty_and_malformed():
    """Empty, NaN, N/A, and malformed inputs must return empty strings or safe fallback without crash."""
    assert normalize_url(None) == ""
    assert normalize_url("N/A") == ""
    assert normalize_url("   ") == ""
    assert normalize_url("none") == ""
    res = normalize_url("htp://:invalid-url-example#frag")
    assert isinstance(res, str)

def test_url_normalization_duplicate_detection():
    """Equivalent URLs with different tracking params must match after normalization."""
    url1 = "https://www.google.com/maps/place/TestBranch?authuser=0&hl=en"
    url2 = "https://www.google.com/maps/place/TestBranch?utm_source=promo&g_ep=123"
    assert normalize_url(url1) == normalize_url(url2)


# =====================================================================
# PART 2: Safe Locator & CSS Escape Tests (Requirement B)
# =====================================================================

def test_css_escape_special_characters():
    """Verify that quotes and backslashes are escaped safely."""
    assert css_escape('Cafe "Le Petit"') == 'Cafe \\"Le Petit\\"'
    assert css_escape("O'Connor's & Co.") == "O'Connor's & Co."
    assert css_escape('Back\\Slash') == 'Back\\\\Slash'


# =====================================================================
# PART 3: Genuine Production Extraction Tests (Revision 3.1.1 & 3.1.2)
# Calling scraper.extract_business_detail() directly
# =====================================================================

class MockLocator:
    def __init__(self, elements=1, can_click=True, fail_first_times=0, error_msg="Detached",
                 aria_label="Address: 123 Main St, Jakarta", href="https://mybusiness.example.com",
                 inner_text="Resolved Business Name"):
        self._count = elements
        self._can_click = can_click
        self._fail_first_times = fail_first_times
        self._attempts = 0
        self._error_msg = error_msg
        self._aria_label = aria_label
        self._href = href
        self._inner_text = inner_text

    async def count(self):
        return self._count

    @property
    def first(self):
        return self

    async def scroll_into_view_if_needed(self, timeout=5000):
        self._attempts += 1
        if self._attempts <= self._fail_first_times:
            raise RuntimeError(self._error_msg)
        if not self._can_click:
            raise RuntimeError(self._error_msg)
        return None

    async def click(self, timeout=5000):
        if not self._can_click:
            raise RuntimeError(self._error_msg)
        return None

    async def get_attribute(self, attr):
        if attr == "aria-label":
            return self._aria_label
        elif attr == "href":
            return self._href
        return None

    async def inner_text(self):
        return self._inner_text


class MockPage:
    def __init__(self, selector_map=None, default_count=1, page_url="https://www.google.com/maps/place/Test+Place"):
        self.url = page_url
        self._selector_map = selector_map or {}
        self._default_count = default_count

    def locator(self, sel):
        if sel in self._selector_map:
            val = self._selector_map[sel]
            # Support callable factories for dynamic per-call locator instances
            if callable(val):
                return val()
            return val
        # Common detail element handlers
        if sel.startswith("button[data-item-id"):
            return MockLocator(elements=1, aria_label="Address: 123 Main St, Jakarta")
        if sel.startswith("a[data-item-id"):
            return MockLocator(elements=1, href="https://mybusiness.example.com")
        if sel == "h1.DUwDvf":
            return MockLocator(elements=1, inner_text="Resolved Business Name")
        return MockLocator(elements=self._default_count)

    def get_by_role(self, role, name=None, exact=False):
        key = f"role_{role}_{name}"
        if key in self._selector_map:
            val = self._selector_map[key]
            if callable(val):
                return val()
            return val
        return MockLocator(elements=self._default_count)

    async def wait_for_timeout(self, ms):
        pass


def test_production_extract_exact_anchor_href_matching():
    """Revision 3.1.1: Direct anchor matching using exact href attribute."""
    async def _test():
        raw_href = "https://www.google.com/maps/place/Cafe+One?authuser=0"
        expected_sel = f'a.hfpxzc[href="{css_escape(raw_href)}"]'
        mock_loc = MockLocator(elements=1)

        page = MockPage(selector_map={expected_sel: mock_loc})
        target = {
            "name": "Cafe One",
            "raw_href": raw_href,
            "norm_href": "https://www.google.com/maps/place/cafe+one"
        }
        res = await extract_business_detail(page, target, index=1, total_targets=1)
        assert res is not None
        assert res["Name"] == "Cafe One"
        assert mock_loc._attempts == 1
    asyncio.run(_test())

def test_production_extract_dom_replacement_retry_succeeds():
    """
    Revision 3.1.2 Test 1 — Actual DOM Replacement:
    1. First call to page.locator() returns locator A.
    2. Locator A raises a simulated DOM-detachment error.
    3. Second call to page.locator() returns a NEW locator B.
    4. Locator B represents the replacement DOM element and succeeds.
    5. Assert that two different locator instances were created.
    6. Assert that extraction succeeds with the expected business data.
    """
    async def _test():
        raw_href = "https://www.google.com/maps/place/Replaced+Target"
        expected_sel = f'a.hfpxzc[href="{css_escape(raw_href)}"]'

        # Locator A: initial element that is detached from DOM
        locator_a = MockLocator(
            elements=1,
            can_click=False,
            error_msg="ElementHandle.scroll_into_view_if_needed: Element is not attached to the DOM"
        )
        # Locator B: new replacement DOM element that succeeds
        locator_b = MockLocator(
            elements=1,
            can_click=True,
            aria_label="Address: Jl. Sudirman Baru No. 10",
            href="https://replaced-target.example.com"
        )

        created_locators = []
        def locator_factory():
            if len(created_locators) == 0:
                loc = locator_a
            else:
                loc = locator_b
            created_locators.append(loc)
            return loc

        page = MockPage(
            selector_map={expected_sel: locator_factory},
            page_url=raw_href
        )
        target = {
            "name": "Replaced Target",
            "raw_href": raw_href,
            "norm_href": "https://www.google.com/maps/place/replaced+target"
        }

        # Calls the actual production function
        res = await extract_business_detail(page, target, index=1, total_targets=1, max_retries=3)

        # Assertions
        assert res is not None
        assert res["Name"] == "Replaced Target"
        assert res["Google Maps URL"] == raw_href
        # Verify two distinct locator instances were created and returned across calls
        assert len(created_locators) == 2
        assert created_locators[0] is locator_a
        assert created_locators[1] is locator_b
        assert created_locators[0] is not created_locators[1]
        assert locator_a._attempts == 1
        assert locator_b._attempts == 1
    asyncio.run(_test())

def test_production_extract_special_characters_escaping():
    """Revision 3.1.1: Business names and URLs with quotes, apostrophes, ampersands, and brackets."""
    async def _test():
        target_name = 'L\'Artisan & "Bistro" #1 [Bandung]'
        raw_href = 'https://www.google.com/maps/place/L%27Artisan+%26+%22Bistro%22'
        escaped_href = css_escape(raw_href)
        expected_sel = f'a.hfpxzc[href="{escaped_href}"]'
        mock_loc = MockLocator(elements=1)

        page = MockPage(selector_map={expected_sel: mock_loc})
        target = {
            "name": target_name,
            "raw_href": raw_href,
            "norm_href": "https://www.google.com/maps/place/l%27artisan"
        }
        res = await extract_business_detail(page, target, index=1, total_targets=1)
        assert res is not None
        assert res["Name"] == target_name
    asyncio.run(_test())

def test_production_extract_two_branches_correct_branch_selection_by_url():
    """
    Revision 3.1.2 Test 2 — Same DOM, Same Business Name, Different Branch URLs:
    Create one mock page representing a DOM containing two anchor elements:
    - Starbucks Downtown
    - Starbucks Uptown
    Both have the identical business name ('Starbucks'), but their href values are different.
    Call extract_business_detail() for each target URL against the SAME page.
    Verify:
    - The correct anchor is selected by its URL.
    - The wrong branch is never selected.
    - The returned Google Maps URL matches the intended branch.
    - Name fallback is not used when a reliable URL match exists.
    """
    async def _test():
        downtown_href = "https://www.google.com/maps/place/Starbucks+Downtown"
        uptown_href = "https://www.google.com/maps/place/Starbucks+Uptown"
        business_name = "Starbucks"

        # Anchors in the same DOM
        loc_downtown = MockLocator(
            elements=1,
            aria_label="Starbucks",
            href=downtown_href
        )
        loc_uptown = MockLocator(
            elements=1,
            aria_label="Starbucks",
            href=uptown_href
        )

        # Ambiguous aria-label locator representing the 2 same-name anchors in the DOM
        loc_ambiguous_name = MockLocator(elements=2)

        # One single page containing both anchors
        shared_page = MockPage(
            selector_map={
                f'a.hfpxzc[href="{css_escape(downtown_href)}"]': loc_downtown,
                f'a.hfpxzc[href="{css_escape(uptown_href)}"]': loc_uptown,
                f'a.hfpxzc[aria-label="{css_escape(business_name)}"]': loc_ambiguous_name,
            },
            page_url="https://www.google.com/maps/search/Starbucks"
        )

        target_downtown = {"name": business_name, "raw_href": downtown_href}
        target_uptown = {"name": business_name, "raw_href": uptown_href}

        # Extract Downtown branch
        res_downtown = await extract_business_detail(shared_page, target_downtown, index=1, total_targets=2)
        # Extract Uptown branch
        res_uptown = await extract_business_detail(shared_page, target_uptown, index=2, total_targets=2)

        # Assertions
        assert res_downtown is not None
        assert res_uptown is not None

        # Verify correct branch selected by URL
        assert res_downtown["Google Maps URL"] == downtown_href
        assert res_uptown["Google Maps URL"] == uptown_href
        assert res_downtown["Name"] == "Starbucks"
        assert res_uptown["Name"] == "Starbucks"
        assert res_downtown["Google Maps URL"] != res_uptown["Google Maps URL"]

        # Verify attempts: each specific URL locator was clicked once
        assert loc_downtown._attempts == 1
        assert loc_uptown._attempts == 1
        # Name fallback was NOT invoked because reliable URL matching succeeded directly
        assert loc_ambiguous_name._attempts == 0
    asyncio.run(_test())

def test_production_extract_ambiguous_name_fallback_fails_safely():
    """
    Revision 3.1.1: If URL is missing and multiple same-name branches exist,
    must NOT silently select the first business.
    """
    async def _test():
        target_name = "Kopi Kenangan"
        # When URL is missing, it falls back to aria-label
        # Here 2 branches exist with identical name
        ambiguous_loc = MockLocator(elements=2)
        page = MockPage(selector_map={f'a.hfpxzc[aria-label="{css_escape(target_name)}"]': ambiguous_loc})

        target = {"name": target_name, "raw_href": None, "norm_href": ""}
        # Should raise ambiguity error inside and exhaust retries, returning None safely
        res = await extract_business_detail(page, target, index=1, total_targets=1, max_retries=2)
        assert res is None
    asyncio.run(_test())

def test_production_extract_retry_exhaustion_returns_none():
    """Revision 3.1.1: Permanent failure exhausts retries and returns None without crashing."""
    async def _test():
        failing_loc = MockLocator(elements=1, can_click=False, error_msg="Permanent DOM error")
        raw_href = "https://www.google.com/maps/place/Broken"
        page = MockPage(selector_map={f'a.hfpxzc[href="{css_escape(raw_href)}"]': failing_loc})

        target = {
            "name": "Broken Target",
            "raw_href": raw_href,
            "norm_href": "https://www.google.com/maps/place/broken"
        }
        res = await extract_business_detail(page, target, index=1, total_targets=1, max_retries=3)
        assert res is None
        assert failing_loc._attempts == 3
    asyncio.run(_test())


# =====================================================================
# PART 4: Processor & Excel Deduplication Regression Tests
# =====================================================================

def test_dedup_duplicate_urls_different_params(tmp_path, monkeypatch):
    records = [
        {"No": 1, "Name": "Cafe A", "Address": "Jl. A", "Phone": "111", "Website": "N/A", "Google Maps URL": "https://www.google.com/maps/place/CafeA?authuser=0"},
        {"No": 2, "Name": "Cafe A", "Address": "Jl. A", "Phone": "111", "Website": "N/A", "Google Maps URL": "https://www.google.com/maps/place/CafeA?utm_source=feed"},
    ]
    monkeypatch.chdir(tmp_path)
    save_data(records, "test_url_params")
    files = list(tmp_path.glob("*.xlsx"))
    assert len(files) == 1
    df = pd.read_excel(files[0])
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "Cafe A"

def test_dedup_different_branches_same_name(tmp_path, monkeypatch):
    records = [
        {"No": 1, "Name": "Starbucks", "Address": "Branch 1", "Phone": "111", "Website": "N/A", "Google Maps URL": "https://www.google.com/maps/place/Starbucks1"},
        {"No": 2, "Name": "Starbucks", "Address": "Branch 2", "Phone": "222", "Website": "N/A", "Google Maps URL": "https://www.google.com/maps/place/Starbucks2"},
    ]
    monkeypatch.chdir(tmp_path)
    save_data(records, "test_branches")
    files = list(tmp_path.glob("*.xlsx"))
    df = pd.read_excel(files[0])
    assert len(df) == 2
    assert list(df["Address"]) == ["Branch 1", "Branch 2"]

def test_insufficient_identity_records_preserved(tmp_path, monkeypatch):
    records = [
        {"No": 1, "Name": "N/A", "Address": "N/A", "Phone": "111", "Website": "N/A", "Google Maps URL": "N/A"},
        {"No": 2, "Name": "N/A", "Address": "N/A", "Phone": "222", "Website": "N/A", "Google Maps URL": "N/A"},
        {"No": 3, "Name": None, "Address": None, "Phone": "333", "Website": "N/A", "Google Maps URL": None},
    ]
    monkeypatch.chdir(tmp_path)
    save_data(records, "test_insufficient_identity")
    files = list(tmp_path.glob("*.xlsx"))
    df = pd.read_excel(files[0])
    assert len(df) == 3

def test_excel_export_schema_and_counts(tmp_path, monkeypatch):
    records = [
        {"No": 1, "Name": "Business A", "Address": "123 Main St", "Phone": "555-1234", "Website": "http://a.com", "Google Maps URL": "https://maps.google.com/1"},
        {"No": 2, "Name": "Business B", "Address": "456 Side St", "Phone": "555-5678", "Website": "http://b.com", "Google Maps URL": "https://maps.google.com/2"},
    ]
    monkeypatch.chdir(tmp_path)
    save_data(records, "test_schema")
    files = list(tmp_path.glob("*.xlsx"))
    df = pd.read_excel(files[0])
    expected_cols = ["No", "Name", "Address", "Phone", "Website", "Google Maps URL"]
    assert list(df.columns) == expected_cols
    assert list(df["No"]) == [1, 2]
    assert len(df) == 2
