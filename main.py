import asyncio
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- Google Sheets Setup [cite: 8, 35] ---
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("TikTok_Ads_Data").get_worksheet(0)

# --- Classificatie Logica (Phase 5 & 6) [cite: 3, 36, 37] ---
def classify_ad(text):
    text = text.lower()
    angle = "Problem" if any(w in text for w in ["tired", "struggle", "fix"]) else "Desire"
    hook = "POV" if "pov" in text else "Visual"
    return angle, hook

async def run():
    sheet = get_sheet()
    async with async_playwright() as p:
        # Gebruik extra argumenten om 'headless' detectie te minimaliseren 
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = await context.new_page()

        # Luister naar de API (Phase 3) [cite: 34]
        async def handle_response(response):
            if "creative_radar_api/v1/top_ads/v2/list" in response.url:
                data = await response.json()
                materials = data.get("data", {}).get("materials", [])
                
                rows = []
                for ad in materials:
                    desc = ad.get("ad_description", "")
                    stats = ad.get("stats", {})
                    angle, hook = classify_ad(desc)
                    # Data Model [cite: 35]
                    rows.append([ad.get("ad_id"), desc, stats.get("like_count"), hook, angle])
                
                if rows:
                    sheet.append_rows(rows)
                    print(f"✅ {len(rows)} ads naar Google Sheets geschreven.")

        page.on("response", handle_response)
        
        # Navigeer met een vertraging om de blokkade te vermijden 
        try:
            await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", wait_until="networkidle")
            await page.mouse.wheel(0, 2000) # Forceer data-inlaad
            await asyncio.sleep(5)
        finally:
            await page.screenshot(path="tiktok_debug.png")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
