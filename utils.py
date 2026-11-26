"""
utils.py
Common helper functions for G-LANCE PRO.
Avoids code duplication and circular dependencies between scraper and processor.
"""
import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

# Known tracking/session parameters that do not indicate distinct business identity
KNOWN_TRACKING_PARAMS = {
    "authuser",
    "hl",
    "gl",
    "entry",
    "g_ep",
    "rclk",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ved",
    "source",
}

def normalize_text(text):
    """Trims whitespace and lowercases text for robust matching."""
    if text is None:
        return ""
    try:
        import pandas as pd
        if pd.isna(text):
            return ""
    except ImportError:
        pass
    t = str(text).strip().lower()
    return "" if t in ("n/a", "none", "nan") else t

def normalize_url(url):
    """
    Safely normalizes Google Maps URLs:
    1. Trims whitespace.
    2. Returns empty string for None, NaN, N/A, or equivalent empty inputs.
    3. Normalizes URL scheme and hostname to lowercase.
    4. Preserves path case.
    5. Strips trailing slashes from path where appropriate.
    6. Removes URL fragments (#).
    7. Removes only explicitly identified tracking parameters (e.g. authuser, hl, utm_*).
    8. Preserves unknown/identifying query parameters.
    9. Handles malformed URLs safely without crashing.
    """
    if url is None:
        return ""
    try:
        import pandas as pd
        if pd.isna(url):
            return ""
    except ImportError:
        pass

    raw = str(url).strip()
    if not raw or raw.lower() in ("n/a", "none", "nan"):
        return ""

    try:
        parsed = urlparse(raw)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # If scheme or netloc are missing but it's a relative URL or malformed string
        if not scheme and not netloc and not parsed.path.startswith("/"):
            # Fallback for plain invalid strings
            return raw.rstrip("/").split("#")[0]

        # Path: preserve case, strip trailing slash if length > 1
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

        # Query: filter only known tracking parameters, preserve others
        filtered_query = ""
        if parsed.query:
            query_items = parse_qsl(parsed.query, keep_blank_values=True)
            kept_items = [
                (k, v) for k, v in query_items
                if k.lower() not in KNOWN_TRACKING_PARAMS and not k.lower().startswith("utm_")
            ]
            if kept_items:
                # Sort kept parameters for stable canonical comparison
                kept_items.sort(key=lambda x: (x[0], x[1]))
                filtered_query = urlencode(kept_items)

        # Fragment: strictly removed
        fragment = ""

        normalized = urlunparse((scheme, netloc, path, parsed.params, filtered_query, fragment))
        return normalized.rstrip("/")
    except Exception:
        # Fallback safe handling for any unexpected parsing exception
        return raw.split("?")[0].split("#")[0].rstrip("/")
