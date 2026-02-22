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
        print("🌐 Browser opstarten in stealth mode...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # We registreren een listener die wacht tot de ECHTE TikTok site de API aanroept
        print("🚀 Sessie opwarmen en wachten op natuurlijke API-stroom...")
        
        ads_found = []

        async def intercept_response(response):
            if "top_ads/v2/list" in response.url:
                try:
                    if response.status == 200:
                        data = await response.json()
                        materials = data.get("data", {}).get("materials", [])
                        if materials:
                            print(f"✨ API GEKAAST! {len(materials)} ads onderschept.")
                            for ad in materials:
                                ads_found.append(analyze_ad(ad))
                except Exception:
                    pass

        page.on("response", intercept_response)

        try:
            # We gaan naar de pagina, maar we negeren de visuele blokkade (het slotje)
            # Omdat de API call vaak direct bij het laden gebeurt, vangen we hem hier
            print("📡 Navigeren naar doelsectie...")
            await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", 
                            wait_until="commit", timeout=60000)
            
            # We wachten 20 seconden. Zelfs als er een slotje staat, 
            # heeft de browser op de achtergrond vaak al de eerste API-call gedaan.
            for i in range(10):
                if ads_found: break
                print(f"Wachten op data... ({i+1}/10)")
                await asyncio.sleep(2)
                # We proberen de pagina te 'poken' met JS om calls te forceren
                await page.evaluate("window.scrollTo(0, 500)")

            if ads_found and sheet:
                sheet.append_rows(ads_found)
                print(f"📊 {len(ads_found)} rijen succesvol naar Google Sheets gepusht!")
            else:
                print("⚠️ Geen data kunnen kapen. De beveiligingsmuur is te dik voor dit IP.")
                await page.screenshot(path="failed_intercept.png")

        except Exception as e:
            print(f"❌ Fout tijdens kaping: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
