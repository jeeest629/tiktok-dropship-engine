import asyncio
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- GOOGLE SHEETS SETUP (Fase 4) ---
def get_sheet():
    try:
        # Gebruikt de credentials uit de GitHub Secrets [cite: 15, 16]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(creds)
        # Zorg dat de naam exact 'TikTok_Ads_Data' is of pas dit aan [cite: 35]
        return client.open("TikTok_Ads_Data").get_worksheet(0)
    except Exception as e:
        print(f"❌ Google Sheets Connectie Fout: {e}")
        return None

# --- CLASSIFICATIE & ANALYSE (Fase 5 & 6) ---
def analyze_ad(text, stats):
    text = text.lower()
    # Angle Detection: Problem vs Desire [cite: 37]
    angle = "Problem" if any(w in text for w in ["tired", "struggle", "fix", "bad"]) else "Desire"
    # Hook Classification [cite: 36]
    hook = "POV" if "pov" in text else "Question" if "?" in text else "Visual"
    
    likes = stats.get('like_count', 0)
    velocity = "High" if likes > 5000 else "Medium"
    
    return angle, hook, velocity

async def run():
    sheet = get_sheet()
    
    async with async_playwright() as p:
        print("Browser opstarten met stealth instellingen...")
        browser = await p.chromium.launch(
            headless=True, 
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        # Phase 3: Interceptie van de 'Creative Radar' API [cite: 34]
        async def handle_response(response):
            if "creative_radar_api/v1/top_ads/v2/list" in response.url:
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    print(f"🚀 API data onderschept: {len(materials)} ads gevonden.")
                    
                    rows_to_insert = []
                    for ad in materials:
                        desc = ad.get("ad_description", "")
                        stats = ad.get("stats", {})
                        angle, hook, velocity = analyze_ad(desc, stats)
                        
                        # Data Model voor Google Sheets [cite: 35]
                        rows_to_insert.append([
                            ad.get("ad_id"), 
                            desc[:100], # Eerste 100 tekens van de beschrijving
                            stats.get("play_count", 0), 
                            stats.get("like_count", 0),
                            hook, 
                            angle, 
                            velocity
                        ])
                    
                    if sheet and rows_to_insert:
                        sheet.append_rows(rows_to_insert)
                        print(f"✅ {len(rows_to_insert)} rijen toegevoegd aan Google Sheets.")
                except Exception as e:
                    print(f"⚠️ Fout bij API verwerking: {e}")

        page.on("response", handle_response)

        try:
            print("Navigeren naar Top Ads sectie...")
            # Oplossing voor de timeout: gebruik 'domcontentloaded' ipv 'networkidle' 
            await page.goto(
                "https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", 
                wait_until="domcontentloaded", 
                timeout=60000 # Verhoogde timeout naar 60 seconden
            )
            
            # Geef de pagina de tijd om de API-calls te doen na de initiële load
            print("Wachten op data-activiteit...")
            await asyncio.sleep(15) 
            
            # Forceer scrollen om 'lazy loading' en extra API-calls te triggeren
            print("Scrollen om extra ads te laden...")
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Navigatie mislukt: {e}")
        finally:
            # Sla de debug screenshot ALTIJD op [cite: 31, 33]
            await page.screenshot(path="tiktok_debug.png")
            print("📸 Debug screenshot opgeslagen.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
