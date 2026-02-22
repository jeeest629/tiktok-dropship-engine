import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Start de browser (headless voor snelheid in GitHub Actions)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()

        # Functie om de API-respons te vangen
        async def handle_response(response):
            if "top_ads/v2/list" in response.url:
                try:
                    payload = await response.json()
                    materials = payload.get("data", {}).get("materials", [])
                    
                    print(f"\n✅ API Gevonden! Aantal ads in deze batch: {len(materials)}")
                    
                    if materials:
                        first_ad = materials[0]
                        print("\n--- INSPECTIE EERSTE AD ---")
                        print(f"Beschikbare keys: {list(first_ad.keys())}")
                        # Print een kleine preview van de data
                        print(json.dumps(first_ad, indent=2)[:500] + "...") 
                        print("---------------------------\n")
                except Exception as e:
                    print(f"⚠️ Error bij parsen API: {e}")

        # Luister naar alle netwerk responses
        page.on("response", handle_response)

        print("Navigeren naar TikTok Creative Center...")
        # Gebruik domcontentloaded om timeouts te voorkomen bij oneindig ladende pagina's
        await page.goto("https://ads.tiktok.com/business/creativecenter/topads/pc/en", wait_until="domcontentloaded")
        
        # Wacht even zodat de API-call de tijd heeft om te voltooien
        await page.wait_for_timeout(10000) 
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
