import asyncio
import json
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- GOOGLE SHEETS SETUP ---
def get_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(creds)
        # Zorg dat de sheet 'TikTok_Ads_Data' bestaat 
        return client.open("TikTok_Ads_Data").get_worksheet(0)
    except Exception as e:
        print(f"❌ Sheets Fout: {e}")
        return None

# --- ANALYSE LOGICA (Phase 5, 6 & 7) ---
def analyze_ad(ad):
    desc = ad.get("ad_description", "").lower()
    stats = ad.get("stats", {})
    # Hook & Angle detectie [cite: 36, 37]
    angle = "Problem" if any(w in desc for w in ["tired", "fix", "solution"]) else "Desire"
    hook = "POV" if "pov" in desc else "Question" if "?" in desc else "Standard"
    bundle = "Yes" if "buy" in desc or "get" in desc else "No" # [cite: 38]
    return angle, hook, bundle

async def run():
    sheet = get_sheet()
    async with async_playwright() as p:
        # We gebruiken een browser alleen voor de sessie-context [cite: 10]
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = await context.new_page()

        # 1. Bouw sessie op Trends pagina (vrij toegankelijk) 
        print("Sessie initialiseren...")
        await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", wait_until="domcontentloaded")
        await asyncio.sleep(5)

        # 2. FORCEER API CALL via JavaScript injectie
        # Dit is de 'echte' API methode: we vragen de data aan via de browser-console
        print("🚀 Forceer API Fetch naar Top Ads data...")
        api_url = "https://ads.tiktok.com/business/creativecenter/creative_radar_api/v1/top_ads/v2/list?period=30&region=US&limit=20"
        
        raw_data = await page.evaluate(f"""
            async (url) => {{
                const response = await fetch(url);
                return await response.json();
            }}
        """, api_url)

        # 3. VERWERK DATA [cite: 34]
        materials = raw_data.get("data", {}).get("materials", [])
        if materials:
            print(f"✅ Succes! {len(materials)} ads onderschept.")
            rows = []
            for ad in materials:
                angle, hook, bundle = analyze_ad(ad)
                rows.append([
                    ad.get("ad_id"),
                    ad.get("ad_description", "")[:100],
                    ad.get("stats", {}).get("play_count", 0),
                    ad.get("stats", {}).get("like_count", 0),
                    hook, angle, bundle
                ])
            
            if sheet:
                sheet.append_rows(rows)
                print("📊 Data naar Google Sheets geschreven.")
        else:
            print("⚠️ Geen data ontvangen van API. Mogelijk extra authenticatie nodig.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
