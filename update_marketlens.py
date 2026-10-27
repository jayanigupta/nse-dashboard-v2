from playwright.sync_api import sync_playwright
import os

URL = "https://marketlens.nseindia.com/screener?t=3AesV0svI5-lPZ1e2zXxqmBt5GATIsDS8ZmQ3amjMdetQcb8HCElmdiAxHAO0NE34rDmDa1uZBIE__kd_QQ"

OUTPUT_FILE = "marketlens.csv"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()


    print("Opening Market Lens...")

    from playwright.sync_api import Error as PlaywrightError
    import time

    for attempt in range(1, 4):
        try:
            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=120000
            )
            print("Page opened.")
            break

        except PlaywrightError as e:
            print(f"Navigation attempt {attempt}/3 failed: {e}")

            if attempt == 3:
                browser.close()
                raise

            time.sleep(attempt * 5)

    print("Title:", page.title())

    # Give the Market Lens screener time to load its data
    print("Waiting for screener data...")
    page.wait_for_timeout(10000)

    # Check how many table rows are currently visible
    rows = page.locator("tbody tr").count()
    print("Visible table rows:", rows)

    if rows == 0:
        print("ERROR: No screener rows loaded. Not exporting.")
        browser.close()
        raise SystemExit(1)

    print("Exporting Market Lens data...")

    with page.expect_download(timeout=30000) as download_info:
        page.get_by_role(
            "button",
            name="Export"
        ).click()

    download = download_info.value

    print("Downloaded:", download.suggested_filename)

    temp_file = "marketlens_new.csv"
    download.save_as(temp_file)

    # Check that the download actually contains dataf
    with open(temp_file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    print("Downloaded CSV lines:", len(lines))

    if len(lines) <= 1:
        os.remove(temp_file)
        print("ERROR: CSV contains only the header. Existing marketlens.csv was NOT changed.")
        browser.close()
        raise SystemExit(1)

    os.replace(temp_file, OUTPUT_FILE)

    print("Updated:", OUTPUT_FILE)

    browser.close()

print("Market Lens update complete.")
