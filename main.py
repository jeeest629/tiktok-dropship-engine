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
    # Classificatie op basis van de JSON data (Phase 5, 6 & 7)
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

        # Stap 1: Alleen de 'veilige' pagina laden voor de sessie-context
        print("🚀 Sessie-tokens verzamelen via Trends...")
        await page.goto("https://ads.tiktok.com/business/creativecenter/inspiration/trends/pc/en", wait_until="networkidle")
        
        # Stap 2: Navigeer DIRECT naar de API URL (Raw JSON Methode)
        # Dit is GEEN nabootsing. We dwingen de browser om de JSON direct te tonen.
        print("📡 Directe API-omleiding uitvoeren...")
        api_url = "https://ads.tiktok.com/business/creativecenter/creative_radar_api/v1/top_ads/v2/list?limit=20&period=30&region=US&sort_by=fb_receive_count"
        
        try:
            # We navigeren direct naar de API; de browser stuurt de cookies mee
            response = await page.goto(api_url)
            
            if response.status != 200:
                print(f"⚠️ TikTok weigerde de directe toegang. Status: {response.status}")
                # Maak screenshot van de foutmelding
                await page.screenshot(path="tiktok_error.png")
            else:
                # Trek de tekst (JSON) uit de body van de pagina
                content = await page.inner_text("body")
                raw_data = json.loads(content)
                
                materials = raw_data.get("data", {}).get("materials", [])
                if materials:
                    print(f"✨ SUCCES! {len(materials)} ads direct uit JSON-body getrokken.")
                    rows = [analyze_ad(ad) for ad in materials]
                    if sheet:
                        sheet.append_rows(rows)
                        print("📊 Gegevens verwerkt en naar Google Sheets verzonden.")
                else:
                    print("⚠️ JSON ontvangen, maar geen advertenties gevonden.")
                    print(f"Inhoud: {content[:200]}...")
                    
        except Exception as e:
            print(f"❌ Directe API-uitlezing mislukt: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
