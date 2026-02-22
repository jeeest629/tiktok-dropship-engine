import asyncio
import json
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

def get_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(creds)
        return client.open("TikTok_Ads_Data").get_worksheet(0)
    except Exception as e:
        print(f"❌ Sheets Fout: {e}")
        return None

def analyze_ad(ad):
    desc = ad.get("ad_description", "").lower()
    stats = ad.get("stats", {})
    # Phase 6: Angle Detection [cite: 37]
    angle = "Problem" if any(w in desc for w in ["tired", "fix", "solution"]) else "Desire"
    # Phase 5: Hook Classification [cite: 36]
    hook = "POV" if "pov" in desc else "Question" if "?" in desc else "Standard"
    # Phase 7: Bundle Detection [cite: 38]
    bundle = "Yes" if "buy" in desc or "get" in desc else "No"
    return angle, hook, bundle

async def run():
    sheet = get_sheet()
    async with async_playwright() as p:
        # We gebruiken Playwright voor browser automatisering [cite: 10, 33]
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = await context.new_page()

        # Luister naar de API response in plaats van zelf te fetchen 
        async def handle_response(response):
            if "top_ads/v2/list" in response.url:
                try:
                    # Check of het JSON is voordat we parsen
                    if "application/json" in response.headers.get("content-type", ""):
                        payload = await response.json()
                        materials = payload.get("data", {}).get("materials", [])
                        if materials:
                            print(f"✅ Onderschept: {len(materials)} ads.")
                            rows = [[ad.get("ad_id"), ad.get("ad_description", "")[:100], 
                                     ad.get("stats", {}).get("play_count", 0), 
                                     ad.get("stats", {}).get("like_count", 0),
                                     *analyze_ad(ad)] for ad in materials]
                            if sheet:
                                sheet.append_rows(rows)
                                print("📊 Data weggeschreven naar Google Sheets.")
                except Exception as e:
                    print(f"⚠️ Interceptie fout: {e}")

        page.on("response", handle_response)

        print("Sessie opstarten en navigeren...")
        # We navigeren naar de pagina en laten de interne scripts de API aanroepen 
        await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", 
                        wait_until="domcontentloaded")
        
        # Simuleer menselijk gedrag om de API te triggeren 
        for i in range(5):
            await page.mouse.wheel(0, 1000)
            await asyncio.sleep(3)

        await page.screenshot(path="tiktok_debug.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
