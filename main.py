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

# --- 2. ANALYSE LOGICA (Fase 5, 6 & 7) ---
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
        # We gebruiken een context die cookies en headers strikt beheert
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Stap 1: Alleen commit afwachten om cookies te vangen op Trends
        print("🚀 Sessie-initialisatie op Trends...")
        await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", 
                        wait_until="commit", timeout=60000)
        await asyncio.sleep(10) 
        
        # Stap 2: Actieve API-aanroep forceren met gespoofte headers
        # We gebruiken page.evaluate om de browser de request te laten doen
        print("📡 Forceren van geautoriseerde API-fetch...")
        api_url = "https://ads.tiktok.com/business/creativecenter/creative_radar_api/v1/top_ads/v2/list?limit=20&period=30&region=US&sort_by=fb_receive_count"
        
        try:
            # We injecteren een fetch die de Referer header handmatig zet
            raw_data = await page.evaluate(f"""
                async () => {{
                    const response = await fetch('{api_url}', {{
                        "headers": {{
                            "accept": "application/json, text/plain, */*",
                            "referer": "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en",
                            "x-requested-with": "XMLHttpRequest"
                        }},
                        "method": "GET"
                    }});
                    return await response.json();
                }}
            """)
            
            materials = raw_data.get("data", {}).get("materials", [])
            if materials:
                print(f"✨ SUCCES! {len(materials)} ads opgehaald via header-injection.")
                rows = [analyze_ad(ad) for ad in materials]
                if sheet:
                    sheet.append_rows(rows)
                    print("📊 Data weggeschreven naar Google Sheets.")
            else:
                print("⚠️ API antwoordde met lege data. TikTok herkent de fetch als bot.")
                print(f"Debug: {json.dumps(raw_data)[:200]}")
                
        except Exception as e:
            print(f"❌ Header-injection mislukt: {e}")
            await page.screenshot(path="injection_error.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
