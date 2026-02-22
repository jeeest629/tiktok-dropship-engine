from playwright.sync_api import sync_playwright

URL = "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en"

def handle_response(response):
    if "creative_radar_api" in response.url:
        try:
            data = response.json()
            if "data" in data:
                print("API:", response.url)
                print("Has data keys:", list(data["data"].keys()) if isinstance(data["data"], dict) else "list")
        except:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    )
    page = context.new_page()

    page.on("response", handle_response)

    page.goto(URL, wait_until="domcontentloaded", timeout=60000)

    page.wait_for_timeout(8000)

    print("Title:", page.title())

    browser.close()
