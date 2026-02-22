import asyncio
import json
import gspread
import requests
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- 1. GOOGLE SHEETS SETUP ---
def get_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(creds)
        # Zorg dat de sheet 'TikTok_Ads_Data' bestaat in je Drive
        return client.open("TikTok_Ads_Data").get_worksheet(0)
    except Exception as e:
        print(f"❌ Google Sheets Connectie Fout: {e}")
        return None

# --- 2. DATA ANALYSE ENGINE (Phase 5, 6 & 7) ---
def process_ad_data(materials):
    rows = []
    for ad in materials:
        desc = ad.get("ad_description", "").lower()
        stats = ad.get("stats", {})
        
        # Phase 6: Angle Detection
        angle = "Problem" if any(w in desc for w in ["tired", "fix", "solution", "struggle"]) else "Desire"
        
        # Phase 5: Hook Classification
        hook = "POV" if "pov" in desc else "Question" if "?" in desc else "Standard"
        
        # Phase 7: Bundle Detection
        bundle = "Yes" if any(w in desc for w in ["buy", "get", "pack", "set", "off"]) else "No"
        
        rows.append([
            ad.get("ad_id"),
            ad.get("ad_description", "")[:150],
            stats.get("play_count", 0),
            stats.get("like_count", 0),
            hook,
            angle,
            bundle,
            "US" # Regio filter
        ])
    return rows

# --- 3. DE PURE API ENGINE ---
async def run():
    sheet = get_sheet()
    
    async with async_playwright() as p:
        print("🔐 Stap 1: Authenticatie-tokens genereren...")
        browser = await p.chromium.launch(headless=True)
        # We gebruiken een context om alleen de noodzakelijke cookies te vangen
        context = await browser.new_context()
        page = await context.new_page()

        # We gaan naar de login-loze trends pagina om de sessie te 'warmen'
        await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", wait_until="domcontentloaded")
        
        print("🚀 Stap 2: Directe API Request forceren...")
        # We voeren de API call uit via de interne browser-fetch (omzeilt headers/beveiliging)
        api_script = """
        async () => {
            const url = "https://ads.tiktok.com/business/creativecenter/creative_radar_api/v1/top_ads/v2/list?limit=20&period=30&region=US&sort_by=fb_receive_count";
            const res = await fetch(url);
            return await res.json();
        }
        """
        
        try:
            result = await page.evaluate(api_script)
            materials = result.get("data", {}).get("materials", [])
            
            if materials:
                print(f"✅ Data Ontvangen: {len(materials)} advertenties gevonden.")
                
                # Verwerk en schrijf naar Sheets
                data_rows = process_ad_data(materials)
                if sheet:
                    sheet.append_rows(data_rows)
                    print(f"📊 {len(data_rows)} rijen succesvol naar Google Sheets geschreven!")
            else:
                print("⚠️ TikTok gaf een leeg resultaat terug. Waarschijnlijk API-beperking.")
                # Print de ruwe respons voor diagnose in de logs
                print(f"Raw Response: {json.dumps(result)[:500]}")
                
        except Exception as e:
            print(f"❌ API Call mislukt: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
