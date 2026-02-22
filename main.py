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
    angle = "Problem" if any(w in desc for w in ["tired", "fix", "solution"]) else "Desire"
    hook = "POV" if "pov" in desc else "Standard"
    return [ad.get("ad_id"), desc[:100], stats.get("play_count", 0), stats.get("like_count", 0), hook, angle]

# --- 3. CORE ENGINE ---
async def run():
    sheet = get_sheet()
    ads_collected = []

    async with async_playwright() as p:
        print("🌐 Browser opstarten...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = await context.new_page()

        # Interceptor: we luisteren alleen naar wat er binnenkomt
        async def handle_response(response):
            if "top_ads/v2/list" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    materials = data.get("data", {}).get("materials", [])
                    if materials:
                        print(f"✨ API DATA GEVONDEN! {len(materials)} ads onderschept.")
                        for ad in materials:
                            ads_collected.append(analyze_ad(ad))
                except:
                    pass

        page.on("response", handle_response)

        print("🚀 Navigeren naar Trends (veilige zone)...")
        await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", wait_until="networkidle")
        
        # NU HET BELANGRIJKSTE: We klikken via JS op de 'Inspiration' tab of sturen de browser 
        # naar de Top Ads URL maar we verwachten NIET dat de pagina laadt. 
        # We willen alleen dat de scripts de API call maken.
        print("📡 Triggeren van de interne API calls...")
        await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", wait_until="domcontentloaded")
        
        # Wacht maximaal 20 seconden of de interceptor data vangt
        for _ in range(10):
            if ads_collected: break
            await asyncio.sleep(2)
            await page.mouse.wheel(0, 500) # Scrollen kan de call triggeren

        if ads_collected and sheet:
            sheet.append_rows(ads_collected)
            print(f"📊 {len(ads_collected)} rijen naar Google Sheets geschreven!")
        else:
            print("⚠️ Geen data kunnen onderscheppen.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
