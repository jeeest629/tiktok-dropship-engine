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
    ads_collected = []

    async with async_playwright() as p:
        print("🌐 Browser opstarten in High-Stealth mode...")
        # We gebruiken een specifieke browser launch om detectie te minimaliseren
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        
        # Maak een context die een echte gebruiker simuleert
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
        )
        
        page = await context.new_page()

        # Interceptor: Luister naar de API-stroom van TikTok zelf
        async def handle_response(response):
            # De endpoint is dynamisch, we zoeken op een gedeelte van de URL
            if "top_ads/v2/list" in response.url:
                try:
                    if response.status == 200:
                        data = await response.json()
                        materials = data.get("data", {}).get("materials", [])
                        if materials:
                            print(f"✨ DATA GEVONDEN! {len(materials)} ads onderschept.")
                            for ad in materials:
                                ads_collected.append(analyze_ad(ad))
                except Exception:
                    pass

        page.on("response", handle_response)

        print("🚀 Navigeren naar Trends om sessie te vestigen...")
        await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", wait_until="domcontentloaded")
        await asyncio.sleep(5)

        print("📡 Overstappen naar Top Ads (Achtergrond-interceptie)...")
        # We navigeren naar de pagina, maar verwachten niet dat deze visueel laadt
        # De API call wordt vaak direct bij het laden afgevuurd
        try:
            await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", 
                            wait_until="commit", timeout=60000)
            
            # We simuleren 'menselijk' wachten en kleine bewegingen om de scripts te triggeren
            for i in range(15):
                if ads_collected: break
                print(f"Zoeken naar data... ({i+1}/15)")
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(2)

        except Exception as e:
            print(f"⚠️ Navigatie waarschuwing: {e}")

        if ads_collected and sheet:
            # Voorkom duplicaten in de lijst
            unique_ads = list({v[0]: v for v in ads_collected}.values())
            sheet.append_rows(unique_ads)
            print(f"📊 {len(unique_ads)} unieke ads naar Google Sheets geschreven!")
        else:
            print("❌ Geen data kunnen onderscheppen. TikTok blokkeert de data-flow volledig voor dit IP.")
            await page.screenshot(path="final_debug.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
