import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Launch browser met stealth instellingen [cite: 10]
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Gebruik een moderne User-Agent om detectie te voorkomen [cite: 21]
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()

        # Dit is de kern van Phase 3: het vangen van de API response [cite: 34]
        async def handle_response(response):
            # We zoeken specifiek naar de top_ads lijst API
            if "creative_radar_api/v1/top_ads/v2/list" in response.url:
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    
                    if materials:
                        print(f"\n🚀 API DOORBRAAK! Aantal ads gevonden: {len(materials)}")
                        print("\n--- DATA STRUCTUUR (KEYS) ---")
                        # Dit toont ons de velden zoals 'ad_id', 'stats', etc. [cite: 34]
                        print(list(materials[0].keys())) 
                        
                        print("\n--- PREVIEW EERSTE AD DATA ---")
                        # Print de eerste 500 tekens van de ruwe data voor inspectie
                        print(json.dumps(materials[0], indent=2)[:500])
                    else:
                        print("⚠️ API gevonden, maar de 'materials' lijst is leeg.")
                except Exception as e:
                    print(f"⚠️ Fout bij het lezen van API JSON: {e}")

        # Registreer de handler voordat we navigeren
        page.on("response", handle_response)

        print("Navigeren naar TikTok Creative Center...")
        try:
            # Gebruik de basis URL voor de Top Ads [cite: 21]
            await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en", 
                            wait_until="domcontentloaded", 
                            timeout=60000)
            
            # Stap 1: Wacht even op de eerste lading
            await page.wait_for_timeout(5000)
            
            # Stap 2: Scrollen om de API te triggeren (nabootsen gebruiker)
            print("Scrollen om extra data te laden...")
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(5000)

            # Stap 3: Screenshot maken voor debugging (Phase 2) 
            await page.screenshot(path="tiktok_debug.png")
            print("Screenshot 'tiktok_debug.png' opgeslagen.")
            
            # Laatste wachtmoment voor de API
            print("Wachten op finale API-responses...")
            await page.wait_for_timeout(10000)

        except Exception as e:
            print(f"❌ Navigatie of script fout: {e}")
        
        finally:
            await browser.close()
            print("Browser gesloten.")

if __name__ == "__main__":
    asyncio.run(run())
