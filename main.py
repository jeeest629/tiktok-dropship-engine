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
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    cookies_dict = {}

    async with async_playwright() as p:
        print("🌐 Browser opstarten (Ultra-Light mode)...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        # We verhogen de timeout en wachten NIET op networkidle
        print("🚀 Snel cookies oogsten...")
        try:
            await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", 
                            wait_until="commit", timeout=60000)
            # Korte pauze om JS de kans te geven cookies te zetten
            await asyncio.sleep(5) 
            cookies = await context.cookies()
            cookies_dict = {c['name']: c['value'] for c in cookies}
            print(f"🔑 {len(cookies_dict)} sessie-cookies gevonden.")
        except Exception as e:
            print(f"⚠️ Cookie-extractie waarschuwing: {e}")
        finally:
            await browser.close()

    if not cookies_dict:
        print("❌ Geen cookies beschikbaar. Poging zonder cookies via requests...")

    # STAP 2: De feitelijke API aanroep via Requests
    print("📡 Directe API-aanvraag uitvoeren...")
    api_url = "https://ads.tiktok.com/business/creativecenter/creative_radar_api/v1/top_ads/v2/list"
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en",
        "x-requested-with": "XMLHttpRequest",
        "client-type": "PC"
    }
    params = {
        "limit": "20",
        "period": "30",
        "region": "US",
        "sort_by": "fb_receive_count",
        "page": "1"
    }

    try:
        # We gebruiken een session voor betere header-handling
        session = requests.Session()
        response = session.get(api_url, headers=headers, params=params, cookies=cookies_dict, timeout=20)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            materials = data.get("data", {}).get("materials", [])
            
            if materials:
                print(f"✨ SUCCES! {len(materials)} ads gevonden.")
                rows = [analyze_ad(ad) for ad in materials]
                if sheet:
                    sheet.append_rows(rows)
                    print("📊 Data succesvol in Google Sheets!")
            else:
                print("⚠️ API antwoordde met status 200 maar zonder ads.")
                print(f"Respons-preview: {response.text[:200]}")
        else:
            print(f"❌ API Fout {response.status_code}")
            # Maak een dummy screenshot van de situatie (niet mogelijk met requests, maar we loggen de body)
            if "Forbidden" in response.text or response.status_code == 403:
                print("⛔ IP Geblokkeerd door TikTok. Tijd voor een proxy.")

    except Exception as e:
        print(f"❌ Kritieke fout: {e}")

if __name__ == "__main__":
    asyncio.run(run())
