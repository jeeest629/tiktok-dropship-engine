import asyncio
import json
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- 1. GOOGLE SHEETS SETUP ---
def get_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(creds)
        return client.open("TikTok_Ads_Data").get_worksheet(0)
    except Exception as e:
        print(f"❌ Sheets Fout: {e}")
        return None

# --- 2. ANALYSE LOGICA ---
def analyze_ad(ad):
    desc = ad.get("ad_description", "").lower()
    stats = ad.get("stats", {})
    angle = "Problem" if any(w in desc for w in ["tired", "fix", "solution", "struggle"]) else "Desire"
    hook = "POV" if "pov" in desc else "Question" if "?" in desc else "Standard"
    bundle = "Yes" if any(w in desc for w in ["buy", "get", "pack", "set", "off"]) else "No"
    return [ad.get("ad_id"), desc[:150], stats.get("play_count", 0), stats.get("like_count", 0), hook, angle, bundle]

# --- 3. CORE ENGINE ---
async def run():
    sheet = get_sheet()
    
    async with async_playwright() as p:
        print("🌐 Browser opstarten...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Stap 1: Alleen commit afwachten om cookies te vangen
        print("🚀 Sessie-initialisatie starten...")
        try:
            await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", 
                            wait_until="commit", timeout=60000)
            await asyncio.sleep(10) # Handmatige pauze voor cookie-zetting
        except Exception as e:
            print(f"⚠️ Initiële sessie-waarschuwing (we gaan door): {e}")
        
        # Stap 2: Navigeer DIRECT naar de API URL
        print("📡 Directe API-uitlezing forceren...")
        api_url = "https://ads.tiktok.com/business/creativecenter/creative_radar_api/v1/top_ads/v2/list?limit=20&period=30&region=US&sort_by=fb_receive_count"
        
        try:
            # We gaan direct naar de JSON-bron
            response = await page.goto(api_url, wait_until="commit", timeout=60000)
            await asyncio.sleep(5) # Wachten tot JSON gerenderd is

            # Controleer of we JSON hebben of een foutpagina
            content = await page.content()
            if "materials" in content:
                # Playwright rendert JSON vaak in een <pre> tag
                json_text = await page.inner_text("body")
                raw_data = json.loads(json_text)
                
                materials = raw_data.get("data", {}).get("materials", [])
                if materials:
                    print(f"✨ SUCCES! {len(materials)} ads gevonden.")
                    rows = [analyze_ad(ad) for ad in materials]
                    if sheet:
                        sheet.append_rows(rows)
                        print("📊 Data weggeschreven naar Google Sheets.")
                else:
                    print("⚠️ JSON leeg of onjuist formaat.")
            else:
                print("❌ Geen advertentie-data gevonden in de response body.")
                await page.screenshot(path="api_error.png")
                    
        except Exception as e:
            print(f"❌ Kritieke fout bij API-aanroep: {e}")
            await page.screenshot(path="final_error.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
