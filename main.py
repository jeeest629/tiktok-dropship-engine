import asyncio
import json
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- CONFIGURATIE & GOOGLE SHEETS ---
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    client = gspread.authorize(creds)
    # Zorg dat deze sheet bestaat en gedeeld is met je service account mail
    return client.open("TikTok_Ads_Data").get_worksheet(0)

# --- FASE 5 & 6: CLASSIFICATIE LOGICA ---
def classify_ad(text, likes):
    text = text.lower()
    # Angle Detection (Problem vs Desire) [cite: 37]
    angle = "Unknown"
    if any(w in text for w in ["tired of", "struggle", "fix", "stop"]):
        angle = "Problem"
    elif any(w in text for w in ["perfect", "obsessed", "must have", "dream"]):
        angle = "Desire"
    
    # Hook Classification [cite: 36]
    hook = "Standard"
    if "pov" in text: hook = "POV"
    elif "?" in text: hook = "Question"
    
    # Velocity Score (Simple version) [cite: 34]
    velocity = "High" if likes > 10000 else "Medium" if likes > 1000 else "Low"
    
    return angle, hook, velocity

# --- CORE ENGINE ---
async def run():
    sheet = get_sheet()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        async def handle_response(response):
            # Target de Creative Radar API [cite: 33]
            if "creative_radar_api/v1/top_ads/v2/list" in response.url:
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    
                    rows = []
                    for ad in materials:
                        ad_id = ad.get("ad_id")
                        title = ad.get("ad_description", "No Title")
                        likes = ad.get("stats", {}).get("like_count", 0)
                        
                        # Voer classificatie uit 
                        angle, hook, velocity = classify_ad(title, likes)
                        
                        # Bundle Detection (Phase 7) [cite: 38]
                        bundle = "Yes" if "buy 1" in title.lower() or "off" in title.lower() else "No"
                        
                        rows.append([ad_id, title, likes, hook, angle, velocity, bundle])
                    
                    if rows:
                        sheet.append_rows(rows)
                        print(f"✅ {len(rows)} ads gevalideerd en toegevoegd aan de Sheet.")
                except Exception as e:
                    print(f"⚠️ Error: {e}")

        page.on("response", handle_response)

        # Start scraping op het Creative Center [cite: 21, 33]
        await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US&sort_by=fb_receive_count")
        await page.wait_for_timeout(10000)
        
        # Scroll om meer data te triggeren
        for _ in range(3):
            await page.mouse.wheel(0, 1500)
            await page.wait_for_timeout(3000)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
