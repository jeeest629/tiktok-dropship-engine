import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Launch browser met stealth-instellingen om blokkades te voorkomen 
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Gebruik een realistische viewport en User-Agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()

        # Phase 3: Interceptie van de 'Creative Radar' API [cite: 34]
        async def handle_response(response):
            if "creative_radar_api/v1/top_ads/v2/list" in response.url:
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    
                    if materials:
                        print(f"\n🚀 API DOORBRAAK! Ads gevonden: {len(materials)}")
                        print("\n--- BESCHIKBARE DATA VELDEN (KEYS) ---")
                        # Dit toont ons de velden zoals 'ad_id', 'stats', 'video_info' [cite: 34]
                        print(list(materials[0].keys())) 
                        
                        print("\n--- PREVIEW EERSTE AD DATA ---")
                        print(json.dumps(materials[0], indent=2)[:500])
                    else:
                        print("⚠️ De API stuurde een lege lijst met materials.")
                except Exception as e:
                    print(f"⚠️ Fout bij verwerken API JSON: {e}")

        # Registreer de interceptor
        page.on("response", handle_response)

        print("Navigeren naar het Top Ads Dashboard...")
        try:
            # Direct naar de dashboard URL met filters (Periode: 30 dagen, Regio: US) 
            target_url = "https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US"
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wacht specifiek tot de advertentie-kaarten in de DOM verschijnen
            print("Wachten op advertentie-kaarten...")
            try:
                # We zoeken naar een element dat typisch is voor een geladen ad-grid
                await page.wait_for_selector("div[class*='Card']", timeout=20000)
            except:
                print("Waarschuwing: Specifieke ad-selector niet gevonden, we gaan door met scrollen.")

            # Scrollen om extra API calls te forceren (nabootsen gebruiker) 
            print("Scrollen om data-inlaad te forceren...")
            for _ in range(3):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(2000)

            # Sla een nieuwe screenshot op om de huidige staat te verifiëren
            await page.screenshot(path="tiktok_debug.png")
            print("Nieuwe debug screenshot opgeslagen.")
            
            # Geef de API de laatste kans om te antwoorden
            await page.wait_for_timeout(5000)

        except Exception as e:
            print(f"❌ Navigatie fout: {e}")
        
        finally:
            await browser.close()
            print("Browser gesloten.")

if __name__ == "__main__":
    asyncio.run(run())
