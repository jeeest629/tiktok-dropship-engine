import asyncio
import json
import gspread
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# --- GOOGLE SHEETS SETUP (Fase 4) ---
def get_sheet():
    try:
        # Gebruikt de credentials uit de GitHub Secrets [cite: 15, 25]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
        client = gspread.authorize(creds)
        # Zorg dat de sheet 'TikTok_Ads_Data' bestaat [cite: 35]
        return client.open("TikTok_Ads_Data").get_worksheet(0)
    except Exception as e:
        print(f"❌ Sheets Fout: {e}")
        return None

# --- ANALYSE LOGICA (Fase 5, 6 & 7) ---
def analyze_ad(ad):
    desc = ad.get("ad_description", "").lower()
    stats = ad.get("stats", {})
    
    # Fase 6: Angle Detection (Problem vs Desire) [cite: 37]
    angle = "Problem" if any(w in desc for w in ["tired", "fix", "solution", "struggle"]) else "Desire"
    
    # Fase 5: Hook Classification [cite: 36]
    hook = "POV" if "pov" in desc else "Question" if "?" in desc else "Standard"
    
    # Fase 7: Bundle Detection [cite: 38]
    bundle = "Yes" if any(w in desc for w in ["buy", "get", "pack", "set", "off"]) else "No"
    
    return angle, hook, bundle

async def run():
    sheet = get_sheet()
    
    # Gebruik Playwright voor browser automatisering (Fase 2) 
    async with async_playwright() as p:
        print("Browser opstarten...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Passive Interceptor: Luister naar de natuurlijke API respons 
        async def handle_response(response):
            # We zoeken specifiek naar de top_ads lijst 
            if "top_ads/v2/list" in response.url:
                try:
                    # Check of de respons werkelijk JSON is om de 'DOCTYPE' error te voorkomen
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        payload = await response.json()
                        materials = payload.get("data", {}).get("materials", [])
                        
                        if materials:
                            print(f"✅ Onderschept: {len(materials)} ads.")
                            rows = []
                            for ad in materials:
                                angle, hook, bundle = analyze_ad(ad)
                                # Structureren van data voor Google Sheets [cite: 35]
                                rows.append([
                                    ad.get("ad_id"), 
                                    ad.get("ad_description", "")[:100], 
                                    ad.get("stats", {}).get("play_count", 0), 
                                    ad.get("stats", {}).get("like_count", 0),
                                    hook, 
                                    angle, 
                                    bundle
                                ])
                            
                            if sheet and rows:
                                sheet.append_rows(rows)
                                print("📊 Data succesvol weggeschreven naar Google Sheets.")
                except Exception as e:
                    print(f"⚠️ Interceptie fout: {e}")

        page.on("response", handle_response)

        print("Sessie opstarten en navigeren...")
        try:
            # Navigeer naar de pagina; de website zal zelf de API aanroepen [cite: 31, 33]
            await page.goto(
                "https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US", 
                wait_until="domcontentloaded",
                timeout=60000
            )
            
            # Simuleer scrollen om extra API-calls (lazy loading) te triggeren 
            print("Scrollen om data-stroom op gang te brengen...")
            for i in range(5):
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(4) # Geef de API tijd om te antwoorden

        except Exception as e:
            print(f"❌ Fout tijdens navigatie: {e}")
        finally:
            # Altijd een screenshot maken voor debugging 
            await page.screenshot(path="tiktok_debug.png")
            print("📸 Debug screenshot gemaakt.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
