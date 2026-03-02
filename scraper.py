import random
from playwright.async_api import async_playwright
from config import BASE_URL, HEADLESS, SCROLL_COUNT

async def get_google_maps_data(keyword):
    """
    Automates the browser to search and deep-scrape business details.
    """
    async with async_playwright() as p:
        # Launching Chromium with a modern User-Agent to bypass detection
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"🚀 G-LANCE: Initializing Search for '{keyword}'...")
        search_url = f"{BASE_URL}{keyword}"
        
        try:
            # Navigate to Google Maps
            await page.goto(search_url, timeout=60000)
            await page.wait_for_timeout(random.randint(3000, 5000))

            # Automated Scrolling to load results
            print("⏳ LOADING RESULTS: Scrolling through the list...")
            for i in range(SCROLL_COUNT):
                await page.mouse.wheel(0, 3500)
                await page.wait_for_timeout(random.randint(1500, 2500))

            # Select all business card links (Selector: hfpxzc)
            links = await page.query_selector_all('a.hfpxzc')
            
            results = []
            # We take the first 20 links for this session
            target_links = links[:20] 
            print(f"🔎 DISCOVERY: Found {len(links)} leads. Processing top {len(target_links)}...")

            for index, link in enumerate(target_links, start=1):
                try:
                    business_name = await link.get_attribute('aria-label')
                    maps_url = await link.get_attribute('href')
                    
                    # Interaction: Click to open the detail panel
                    await link.scroll_into_view_if_needed()
                    await link.click()
                    
                    # Human-like delay to wait for detail panel to load
                    await page.wait_for_timeout(random.randint(2500, 4500)) 

                    # Locating Data Elements
                    address_loc = page.locator('button[data-item-id="address"]')
                    phone_loc = page.locator('button[data-item-id*="phone"]')
                    website_loc = page.locator('a[data-item-id="authority"]')

                    # Extracting Text/Attributes
                    address = await address_loc.get_attribute('aria-label') if await address_loc.count() > 0 else "N/A"
                    phone = await phone_loc.get_attribute('aria-label') if await phone_loc.count() > 0 else "N/A"
                    website = await website_loc.get_attribute('href') if await website_loc.count() > 0 else "N/A"

                    results.append({
                        "No": index,
                        "Name": business_name,
                        "Address": address.replace("Address: ", "").replace("Alamat: ", ""),
                        "Phone": phone.replace("Phone: ", "").replace("Telepon: ", ""),
                        "Website": website,
                        "Google Maps URL": maps_url
                    })
                    
                    print(f"   ✅ Scraped#{index}: {business_name}")

                except Exception as e:
                    print(f"   ⚠️ Scraped#{index} Warning: Failed to extract detail for an item.")
                    continue
            
            return results

        except Exception as e:
            print(f"❌ SCRAPER ERROR: {e}")
            return []
        finally:
            await browser.close()