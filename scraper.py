import asyncio
import random
import urllib.parse
from playwright.async_api import async_playwright
from config import BASE_URL, HEADLESS, SCROLL_COUNT
from utils import normalize_url

def css_escape(val):
    """Safely escapes quotes and backslashes for CSS attribute selector value matching."""
    if val is None:
        return ""
    s = str(val)
    return s.replace("\\", "\\\\").replace('"', '\\"')

async def extract_business_detail(page, target, index=1, total_targets=1, max_retries=3, feed_locator=None):
    """
    Safely locates, clicks, and extracts business profile details for a target business
    using the current DOM state with bounded retries.

    Args:
        page: Playwright Page object.
        target (dict): Metadata containing 'name', 'raw_href', and 'norm_href'.
        index (int): 1-based index of current business being processed.
        total_targets (int): Total count of unique targets in the batch.
        max_retries (int): Maximum number of retry attempts for DOM detachment / element failures.
        feed_locator: Optional feed locator for scroll recovery during retries.

    Returns:
        dict: Extracted business record or None if extraction exhausted retries.
    """
    target_name = target.get("name", "N/A")
    raw_href = target.get("raw_href")
    norm_href = target.get("norm_href", "")

    for attempt in range(1, max_retries + 1):
        try:
            card_locator = None

            # Strategy 1: Direct anchor attribute matching using exact href
            if raw_href:
                loc_exact = page.locator(f'a.hfpxzc[href="{css_escape(raw_href)}"]')
                if await loc_exact.count() > 0:
                    card_locator = loc_exact.first
                else:
                    # Strategy 1b: Prefix matching base place URL (stripping tracking query parameters)
                    base_path = raw_href.split("?")[0].split("#")[0]
                    if base_path and base_path != "https://www.google.com/maps/place":
                        loc_base = page.locator(f'a.hfpxzc[href^="{css_escape(base_path)}"]')
                        if await loc_base.count() > 0:
                            card_locator = loc_base.first

            # Strategy 2: If URL matching was not available (e.g. missing raw_href),
            # use name matching ONLY when unambiguous (count == 1) to prevent selecting the wrong branch!
            if not card_locator and target_name and target_name != "N/A":
                # Check direct anchor aria-label matching
                loc_aria = page.locator(f'a.hfpxzc[aria-label="{css_escape(target_name)}"]')
                aria_count = await loc_aria.count()
                if aria_count == 1:
                    card_locator = loc_aria.first
                elif aria_count > 1:
                    # Ambiguous! Multiple branches exist with identical name.
                    # Never silently select the first branch when URL identity cannot be verified.
                    raise RuntimeError(
                        f"Ambiguous target: {aria_count} branches found with name '{target_name}' "
                        f"but URL identity cannot be verified."
                    )
                else:
                    # Try get_by_role as secondary fallback if exact aria-label was 0
                    role_loc = page.get_by_role("link", name=target_name, exact=True)
                    role_count = await role_loc.count()
                    if role_count == 1:
                        card_locator = role_loc.first
                    elif role_count > 1:
                        raise RuntimeError(
                            f"Ambiguous target: {role_count} elements found for role 'link' with name '{target_name}'."
                        )

            if not card_locator or (await card_locator.count() == 0):
                raise RuntimeError("Card element not found in current DOM feed")

            # Verify element is attached and visible/scrollable
            await card_locator.scroll_into_view_if_needed(timeout=5000)
            await card_locator.click(timeout=5000)

            # Wait for detail panel to load
            await page.wait_for_timeout(random.randint(2500, 3800))

            # Extract business name from current state
            resolved_name = target_name
            if resolved_name == "N/A":
                title_loc = page.locator('h1.DUwDvf')
                if await title_loc.count() > 0:
                    resolved_name = (await title_loc.first.inner_text()).strip() or "N/A"

            # Locating Data Elements
            address_loc = page.locator('button[data-item-id="address"]')
            phone_loc = page.locator('button[data-item-id*="phone"]')
            website_loc = page.locator('a[data-item-id="authority"]')

            address = "N/A"
            if await address_loc.count() > 0:
                raw_addr = await address_loc.first.get_attribute('aria-label') or ""
                address = raw_addr.replace("Address: ", "").replace("Alamat: ", "").strip() or "N/A"

            phone = "N/A"
            if await phone_loc.count() > 0:
                raw_phone = await phone_loc.first.get_attribute('aria-label') or ""
                phone = raw_phone.replace("Phone: ", "").replace("Telepon: ", "").strip() or "N/A"

            website = "N/A"
            if await website_loc.count() > 0:
                raw_web = await website_loc.first.get_attribute('href') or ""
                website = raw_web.strip() or "N/A"

            maps_url = page.url if page.url and "place" in page.url else (raw_href or "N/A")

            return {
                "No": index,
                "Name": resolved_name,
                "Address": address,
                "Phone": phone,
                "Website": website,
                "Google Maps URL": maps_url
            }

        except Exception as e:
            if attempt < max_retries:
                print(f"   🔄 [{index}/{total_targets}] Retry {attempt}/{max_retries} for '{target_name}': {e}")
                # Recovery: gently scroll feed to trigger DOM re-hydration
                if feed_locator:
                    try:
                        await feed_locator.first.evaluate("el => el.scrollBy(0, -200)")
                        await page.wait_for_timeout(1000)
                        await feed_locator.first.evaluate("el => el.scrollBy(0, 300)")
                    except Exception:
                        pass
                await page.wait_for_timeout(1500)
            else:
                print(f"   ⚠️ [{index}/{total_targets}] Extraction Failure: Failed to extract '{target_name}' after {max_retries} attempts ({e})")
                return None

async def get_google_maps_data(keyword, limit=20, scrolls=5, headless=False):
    """
    Automates the browser to search and deep-scrape business details from Google Maps.
    Defensively handles dynamic DOM updates by storing stable targets and re-locating
    elements dynamically using fresh locators and bounded retries.

    Args:
        keyword (str): Business search query (e.g., 'Coffee Shop New York', 'Cafe & Restaurant Jakarta').
        limit (int): Maximum number of unique business records to process.
        scrolls (int): Number of scroll operations to load search results.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        list[dict]: List of successfully scraped business records.
    """
    playwright_instance = None
    browser = None
    context = None
    page = None

    try:
        # Protect browser initialization
        playwright_instance = await async_playwright().start()
        browser = await playwright_instance.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Complete URL Encoding including slashes using safe=""
        encoded_keyword = urllib.parse.quote(keyword, safe="")
        search_url = f"{BASE_URL}{encoded_keyword}"

        print(f"🚀 G-LANCE: Initializing Search for '{keyword}'...")
        print(f"🔗 TARGET URL: {search_url}")
        print(f"⚙️  CONFIG: Target Limit={limit} | Max Scrolls={scrolls} | Headless={headless}")

        # Navigate to Google Maps
        await page.goto(search_url, timeout=60000)
        await page.wait_for_timeout(random.randint(3000, 5000))

        # Feed Container Identification & Scrolling
        feed_locator = page.locator('div[role="feed"]')
        has_feed = (await feed_locator.count()) > 0

        if not has_feed:
            # Fallback locator for search results container if role="feed" is missing
            alt_feed = page.locator('div.m6QErb.DxyBCb.kA9KIf.dS8AEf')
            if (await alt_feed.count()) > 0:
                feed_locator = alt_feed
                has_feed = True

        print("⏳ LOADING RESULTS: Scrolling through the feed container...")
        last_count = await page.locator('a.hfpxzc').count()
        stagnant_scroll_count = 0

        for i in range(1, scrolls + 1):
            if has_feed:
                # Scroll directly inside the feed container
                try:
                    await feed_locator.first.evaluate("el => el.scrollBy(0, 3000)")
                except Exception:
                    # Graceful fallback to page mouse wheel if feed evaluate fails
                    await page.mouse.wheel(0, 3000)
            else:
                # Graceful fallback if no explicit feed container exists
                await page.mouse.wheel(0, 3000)

            await page.wait_for_timeout(random.randint(1800, 2800))

            current_cards = await page.query_selector_all('a.hfpxzc')
            current_count = len(current_cards)
            delta = current_count - last_count
            delta_str = f"(+{delta} new)" if delta > 0 else "(no change)"
            print(f"   ↳ Scroll {i}/{scrolls}: {current_count} listings detected {delta_str}")

            # Early stopping if enough listings discovered to satisfy limit
            if current_count >= limit:
                print(f"   🎯 Discovered sufficient listings ({current_count} >= {limit}). Proceeding to extraction.")
                break

            # Stagnant detection: stop if no new listings after 3 consecutive scrolls
            if current_count == last_count:
                stagnant_scroll_count += 1
                if stagnant_scroll_count >= 3:
                    print("   ℹ️  No new listings discovered after 3 consecutive scrolls. Stopping scroll.")
                    break
            else:
                stagnant_scroll_count = 0

            last_count = current_count

        # Collect STABLE identifiers instead of retaining stale ElementHandles
        cards = await page.query_selector_all('a.hfpxzc')
        total_discovered = len(cards)

        unique_targets = []
        seen_norm_urls = set()

        for card in cards:
            raw_href = await card.get_attribute('href')
            raw_name = await card.get_attribute('aria-label')
            norm_href = normalize_url(raw_href)

            if norm_href:
                if norm_href not in seen_norm_urls:
                    seen_norm_urls.add(norm_href)
                    unique_targets.append({
                        "name": raw_name or "N/A",
                        "raw_href": raw_href,
                        "norm_href": norm_href
                    })
            else:
                # Preserved if URL is missing
                unique_targets.append({
                    "name": raw_name or "N/A",
                    "raw_href": raw_href,
                    "norm_href": ""
                })

            if len(unique_targets) >= limit:
                break

        unique_target_count = len(unique_targets)
        print(f"\n🔎 DISCOVERY REPORT:")
        print(f"   • Total Discovered Listings : {total_discovered}")
        print(f"   • Unique Listings Selected   : {unique_target_count} (capped at limit {limit})")

        if unique_target_count == 0:
            print("⚠️ No listings found for the search query.")
            return []

        results = []
        successful_count = 0
        failed_count = 0

        # Execute extraction using production extract_business_detail function
        for index, target in enumerate(unique_targets, start=1):
            record = await extract_business_detail(
                page=page,
                target=target,
                index=index,
                total_targets=unique_target_count,
                max_retries=3,
                feed_locator=feed_locator if has_feed else None
            )

            if record:
                # Assign sequence number based on successfully exported items
                record["No"] = len(results) + 1
                results.append(record)
                successful_count += 1
                print(f"   ✅ [{successful_count}/{unique_target_count}] Extracted: {record['Name']}")
            else:
                failed_count += 1

        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   • Discovered businesses     : {total_discovered}")
        print(f"   • Unique processed targets  : {unique_target_count}")
        print(f"   • Successfully extracted    : {successful_count}")
        print(f"   • Extraction failures       : {failed_count}\n")

        return results

    except Exception as e:
        print(f"❌ SCRAPER ERROR: {e}")
        return []

    finally:
        # Safe and robust browser cleanup
        if page:
            try:
                await page.close()
            except Exception:
                pass
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if playwright_instance:
            try:
                await playwright_instance.stop()
            except Exception:
                pass
