import asyncio
import json
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- CONFIGURATIE & GOOGLE SHEETS (Fase 4) ---
def get_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Gebruikt service_account.json aangemaakt door GitHub Actions
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(creds)
        # Zorg dat de naam van de Sheet exact klopt
        return client.open("TikTok_Ads_Data").get_worksheet(0)
    except Exception as e:
        print(f"❌ Google Sheets Fout: {e}")
        return None

# --- FASE 5, 6 & 7: ANALYSE LOGICA ---
def calculate_metrics(ad_data):
    desc = ad_data.get("ad_description", "").lower()
    stats = ad_data.get("stats", {})
    likes = stats.get("like_count", 0)
    
    # Angle Detection (Problem vs Desire)
    angle = "Problem" if any(w in desc for w in ["tired", "struggle", "fix", "solution"]) else "Desire"
    
    # Hook Classification
    hook = "POV" if "pov" in desc else "Question" if "?" in desc else "Benefit"
    
    # Velocity Score (Engagement snelheid)
    velocity = "High" if likes > 10000 else "Medium" if likes > 1000 else "Low"
    
    # Bundle Detection
    is_bundle = "Yes" if any(w in desc for w in ["buy 1", "get 1", "pack", "set"]) else "No"
    
    return angle, hook, velocity, is_bundle

# --- CORE ENGINE ---
async def run():
    sheet = get_sheet()
    
    async with async_playwright() as p:
        print("Browser opstarten met Stealth configuratie...")
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        
        # Gebruik een context die minder op een bot lijkt
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()

        # Interceptor voor de Creative Radar API
        async def handle_response(response):
            if "creative_radar_api/v1/top_ads/v2/list" in response.url:
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    print(f"🚀 API data onderschept: {len(materials)} ads gevonden.")
                    
                    rows = []
                    for ad in materials:
                        angle, hook, velocity, bundle = calculate_metrics(ad)
                        
                        # Data Model voor Google Sheets
                        rows.append([
                            ad.get("ad_id"),
                            ad.get("ad_description", "")[:100],
                            ad.get("stats", {}).get("play_count", 0),
                            ad.get("stats", {}).get("like_count", 0),
                            hook,
                            angle,
                            velocity,
                            bundle
                        ])
                    
                    if sheet and rows:
                        sheet.append_rows(rows)
                        print(f"✅ {len(rows)} ads gelogd naar Google Sheets.")
                except Exception as e:
                    print(f"⚠️ API verwerkingsfout: {e}")

        page.on("response", handle_response)

        try:
            # STAP 1: Navigeer eerst naar Trends (Bypass blokkade)
            print("Sessie initialiseren via Trends pagina...")
            await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", wait_until="domcontentloaded")
            await asyncio.sleep(5)

            # STAP 2: Deep-link naar Top Ads Dashboard
            print("Navigeren naar Top Ads Dashboard...")
            target_url = "https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US"
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            # STAP 3: Interactie om 'menselijkheid' te veinzen en API te triggeren
            print("Scrollen om data te laden...")
            for _ in range(3):
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(3)

        except Exception as e:
            print(f"❌ Script fout: {e}")
        finally:
            # Maak screenshot voor de GitHub Artifacts
            await page.screenshot(path="tiktok_debug.png")
            print("📸 Debug screenshot gemaakt.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
