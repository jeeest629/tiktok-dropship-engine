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
    # Phase 5 & 6: Angle & Hook classification
    angle = "Problem" if any(w in desc for w in ["tired", "fix", "solution", "struggle"]) else "Desire"
    hook = "POV" if "pov" in desc else "Question" if "?" in desc else "Standard"
    # Phase 7: Bundle Detection
    bundle = "Yes" if any(w in desc for w in ["buy", "get", "pack", "set", "off"]) else "No"
    return [ad.get("ad_id"), desc[:150], stats.get("play_count", 0), stats.get("like_count", 0), hook, angle, bundle]

# --- 3. CORE ENGINE ---
async def run():
    sheet = get_sheet()
    
    async with async_playwright() as p:
        print("🌐 Browser opstarten...")
        browser = await p.chromium.launch(headless=True)
        # Gebruik een context met een realistische user agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # STAP 1: Bouw een legitieme sessie op een pagina die WEL werkt
        print("🚀 Sessie initialiseren via Trends...")
        await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", wait_until="networkidle")
        
        # STAP 2: Voer een 'XHR' injectie uit
        # We gebruiken de browser om de API call te doen alsof de website het zelf doet.
        # Dit omzeilt de 'Unexpected end of JSON' omdat de browser de sessie-headers meestuurt.
        print("📡 Actief data opvragen via interne fetch...")
        
        api_url = "https://ads.tiktok.com/business/creativecenter/creative_radar_api/v1/top_ads/v2/list?limit=20&period=30&region=US&sort_by=fb_receive_count"
        
        # We proberen de data op te halen via de browser console
        try:
            raw_data = await page.evaluate(f"""
                async () => {{
                    const response = await fetch('{api_url}');
                    if (!response.ok) return {{ error: response.status }};
                    return await response.json();
                }}
            """)
            
            if "error" in raw_data:
                print(f"⚠️ TikTok blokkeerde de fetch met status: {raw_data['error']}")
            else:
                materials = raw_data.get("data", {}).get("materials", [])
                if materials:
                    print(f"✨ SUCCES! {len(materials)} ads opgehaald.")
                    rows = [analyze_ad(ad) for ad in materials]
                    if sheet:
                        sheet.append_rows(rows)
                        print("📊 Data weggeschreven naar Google Sheets.")
                else:
                    print("⚠️ API antwoordde, maar stuurde geen advertenties.")
                    print(f"Debug Info: {json.dumps(raw_data)[:200]}")
                    
        except Exception as e:
            print(f"❌ Interne fetch mislukt: {e}")

        # Maak altijd een screenshot voor visuele controle in GitHub Artifacts
        await page.screenshot(path="tiktok_debug.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
