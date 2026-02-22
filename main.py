from playwright.sync_api import sync_playwright

URL = "https://ads.tiktok.com/business/creativecenter/topads/pc/en"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    )
    page = context.new_page()

    print("Navigating...")
    response = page.goto(URL, timeout=60000, wait_until="domcontentloaded")

    print("Status:", response.status if response else "No response")
    print("Final URL:", page.url)

    page.wait_for_timeout(8000)

    print("Title:", page.title())

    html = page.content()
    print("HTML length:", len(html))

    browser.close()
