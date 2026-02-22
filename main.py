import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Launch met extra argumenten om detectie te omzeilen
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Gebruik een realistische User-Agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()

        # API Interceptor
        async def handle_response(response):
            if "top_ads/v2/list" in response.url:
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    print(f"\n🚀 API Gevonden! Aantal ads: {len(materials)}")
                    
                    if materials:
                        # Dit is de jackpot: de structuur van de ad data
                        print("\n--- DATA STRUCTUUR (KEYS) ---")
                        print(list(materials[0].keys()))
                        print("--- VOORBEELD DATA (EERSTE 200 TEKENS) ---")
                        print(json.dumps(materials[0])[:200])
                except Exception as e:
                    print(f"⚠️ API parsing error: {e}")

        page.on("response", handle_response)

        print("Navigeren naar TikTok Creative Center...")
        try:
            # We gaan naar de basis URL om minder 'verdacht' over te komen
            await page.goto("https://ads.tiktok.com/business/creativecenter/topads", 
                            wait_until="domcontentloaded", 
                            timeout=60000)
            
            print("Pagina geladen. Wachten op API-responses (15 sec)...")
            await page.wait_for_timeout(15000)
            
            # Maak een screenshot voor debugging (wordt opgeslagen in de runner)
            await page.screenshot(path="tiktok_debug.png")
            print("Screenshot 'tiktok_debug.png' gemaakt.")

        except Exception as e:
            print(f"❌ Fout tijdens navigatie: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
