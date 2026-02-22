from playwright.sync_api import sync_playwright
import json

URL = "https://ads.tiktok.com/business/creativecenter/topads/pc/en"

def handle_response(response):
    if "creative" in response.url and "api" in response.url:
        try:
            data = response.json()
            print("API HIT:", response.url)
            print("Keys:", list(data.keys()))
        except:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    )
    page = context.new_page()

    page.on("response", handle_response)

    page.goto(URL, wait_until="networkidle", timeout=60000)

    page.wait_for_timeout(10000)

    browser.close()
