import asyncio
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- GOOGLE SHEETS SETUP ---
def get_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(creds)
        # Gebruik de exacte naam van je spreadsheet [cite: 35]
        return client.open("TikTok_Ads_Data").get_worksheet(0)
    except Exception as e:
        print(f"❌ Google Sheets Connectie Fout: {e}")
        return None

# --- CLASSIFICATIE & SCORING (Phase 5, 6 & 7) ---
def analyze_ad(text, metrics):
    text = text.lower()
    # Angle Detection [cite: 3, 37]
    angle = "Problem" if any(w in text for w in ["tired", "struggle", "fix"]) else "Desire"
    # Hook Classification [cite: 36]
    hook = "POV" if "pov" in text else "Question" if "?" in text else "Visual"
    # Velocity Score op basis van engagement [cite: 34]
    likes = metrics.get('like_count', 0)
    velocity = "High" if likes > 5000 else "Medium"
    
    return angle, hook, velocity

async def run():
    sheet = get_sheet()
    async with async_playwright() as p:
        print("Browser opstarten...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Intercept API [cite: 33]
        async def handle_response(response):
            if "creative_radar_api/v1/top_ads/v2/list" in response.url:
                try:
                    data = await response.json()
                    materials = data.get("data", {}).get("materials", [])
                    print(f"🚀 API data onderschept: {len(materials)} ads.")
                    
                    rows = []
                    for ad in materials:
                        desc = ad.get("ad_description", "")
                        stats = ad.get("stats", {})
                        angle, hook, velocity = analyze_ad(desc, stats)
                        
                        # Data model voor Sheet [cite: 35]
                        rows.append([
                            ad.get("ad_id"), 
                            desc[:50], 
                            stats.get("play_count"), 
                            stats.get("like_count"),
                            hook, angle, velocity
                        ])
                    
                    if sheet and rows:
                        sheet.append_rows(rows)
                        print("✅ Data succesvol gelogd naar Google Sheets.")
                except Exception as e:
                    print(f"⚠️ Error in API handling: {e}")

        page.on("response", handle_response)

        try:
            print("Navigeren naar Top Ads sectie...")
            # Gebruik de exacte URL om Trends-landing te voorkomen [cite: 31]
            await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", 
                            wait_until="domcontentloaded", timeout=60000)
            
            # Interactie om API te triggeren [cite: 33]
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ Navigatie mislukt: {e}")
        finally:
            # Forceer screenshot voor debug, ongeacht resultaat [cite: 31]
            await page.screenshot(path="tiktok_debug.png")
            print("📸 Debug screenshot 'tiktok_debug.png' gegenereerd.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
