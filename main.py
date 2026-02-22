import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Launch browser met stealth-instellingen
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Gebruik een specifieke context met extra headers
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                "Referer": "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en"
            }
        )
        
        page = await context.new_page()

        # Interceptor voor de Top Ads API
        async def handle_response(response):
            if "creative_radar_api/v1/top_ads/v2/list" in response.url:
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    
                    if materials:
                        print(f"\n🚀 API DOORBRAAK! Ads gevonden: {len(materials)}")
                        print("\n--- BESCHIKBARE DATA VELDEN (KEYS) ---")
                        print(list(materials[0].keys())) 
                        
                        print("\n--- PREVIEW EERSTE AD DATA ---")
                        print(json.dumps(materials[0], indent=2)[:800])
                    else:
                        print("⚠️ API gevonden, maar de material-lijst is leeg.")
                except Exception as e:
                    print(f"⚠️ Fout bij verwerken API JSON: {e}")

        page.on("response", handle_response)

        print("Navigeren naar de Top Ads Deep-Link...")
        try:
            # Directe link met parameters om de juiste API te triggeren
            target_url = "https://ads.tiktok.com/business/creativecenter/topads/pc/en?period=30&region=US&sort_by=fb_receive_count"
            
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # Wacht op de advertentie-kaarten (meestal div's met een 'Card' class)
            print("Wachten op het laden van de advertentie-grid...")
            await page.wait_for_timeout(10000) # Harde pauze voor JS rendering
            
            # Forceer interactie om lazy-loading API's te triggeren
            print("Scrollen voor data-extractie...")
            for i in range(5):
                await page.mouse.wheel(0, 800)
                await page.wait_for_timeout(2000)

            # Sla screenshot op om te zien of we nu wel op de juiste pagina zijn
            await page.screenshot(path="tiktok_debug.png")
            print("Nieuwe debug screenshot 'tiktok_debug.png' gemaakt.")

        except Exception as e:
            print(f"❌ Navigatie fout: {e}")
        
        finally:
            await browser.close()
            print("Browser gesloten.")

if __name__ == "__main__":
    asyncio.run(run())
