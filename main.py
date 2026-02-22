from playwright.sync_api import sync_playwright

URL = "https://ads.tiktok.com/business/creativecenter/topads/pc/en"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(URL, timeout=60000)
    page.wait_for_timeout(5000)

    print("Page loaded")
    print("Title:", page.title())

    html = page.content()
    print("HTML length:", len(html))

    browser.close()
