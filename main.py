import asyncio
import json
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- CONFIGURATIE & GOOGLE SHEETS ---
def get_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes) [cite: 15]
        client = gspread.authorize(creds)
        return client.open("TikTok_Ads_Data").get_worksheet(0) [cite: 35]
    except Exception as e:
        print(f"❌ Google Sheets Fout: {e}")
        return None

# --- FASE 5, 6 & 7: ANALYSE LOGICA ---
def calculate_metrics(ad_data):
    desc = ad_data.get("ad_description", "").lower()
    stats = ad_data.get("stats", {})
    likes = stats.get("like_count", 0) [cite: 34]
    
    # Angle Detection (Problem vs Desire) 
    angle = "Problem" if any(w in desc for w in ["tired", "struggle", "fix", "solution"]) else "Desire"
    
    # Hook Classification 
    hook = "POV" if "pov" in desc else "Question" if "?" in desc else "Benefit"
    
    # Velocity Score
    velocity = "High" if likes > 10000 else "Medium" if likes > 1000 else "Low"
    
    # Bundle Detection 
    is_bundle = "Yes" if any(w in desc for w in ["buy 1", "get 1", "pack", "set"]) else "No"
    
    return angle, hook, velocity, is_bundle

async def run():
    sheet = get_sheet()
    
    async with async_playwright() as p: [cite: 10, 33]
        print("Browser opstarten met Stealth configuratie...")
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()

        # Interceptor voor de API (Phase 3)
        async def handle_response(response):
            if "creative_radar_api/v1/top_ads/v2/list" in response.url: [cite: 34]
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    print(f"🚀 API data onderschept: {len(materials)} ads gevonden.")
                    
                    rows = []
                    for ad in materials:
                        angle, hook, velocity, bundle = calculate_metrics(ad)
                        rows.append([
                            ad.get("ad_id"),
                            ad.get("ad_description", "")[:100],
                            ad.get("stats", {}).get("play_count", 0),
                            ad.get("stats", {}).get("like_count", 0),
                            hook, angle, velocity, bundle
                        ])
                    
                    if sheet and rows:
                        sheet.append_rows(rows) [cite: 3, 35]
                        print(f"✅ {len(rows)} ads gelogd naar Google Sheets.")
                except Exception as e:
                    print(f"⚠️ API verwerkingsfout: {e}")

        page.on("response", handle_response)

        try:
            # Bypass: Start op een veilige pagina
            print("Sessie initialiseren via Trends pagina...")
            await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", wait_until="domcontentloaded")
            await asyncio.sleep(5)

            # Forceer de API call door een regio-switch of filter te simuleren
            print("API triggeren via dashboard navigatie...")
            await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", wait_until="domcontentloaded")
            
            # Interactie om data-inlaad te forceren
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(10)

        except Exception as e:
            print(f"❌ Script fout: {e}")
        finally:
            await page.screenshot(path="tiktok_debug.png")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
