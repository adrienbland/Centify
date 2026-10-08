import asyncio
from playwright.async_api import async_playwright

class TrendScraper:
    """
    Scraper automatisé pour détecter les tendances produits sur TikTok.
    Conçu pour trouver les produits viraux avant qu'ils ne soient saturés.
    """
    def __init__(self, headless=True):
        self.headless = headless
        
    async def get_trending_videos(self, hashtag="tiktokmademebuyit", max_results=10):
        """
        Scrape les vidéos récentes d'un hashtag spécifique pour extraire :
        - Le lien de la vidéo
        - Le nombre de vues
        - La description (pour y trouver des noms de produits)
        """
        print(f"[TrendScraper] Lancement de l'analyse sur le hashtag #{hashtag}...")
        results = []
        
        async with async_playwright() as p:
            # Lancement d'un navigateur Chromium (peut être couplé avec playwright-stealth si besoin)
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Aller sur la page du hashtag TikTok
            url = f"https://www.tiktok.com/tag/{hashtag}"
            print(f"[TrendScraper] Navigation vers {url}")
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Scroll pour charger les vidéos
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 1000);")
                    await page.wait_for_timeout(2000)
                
                # Extraction des éléments vidéos
                # Note: Les sélecteurs TikTok changent souvent, c'est une architecture conceptuelle
                # que le Hub Laravel appellera régulièrement (Cron Job).
                video_elements = await page.query_selector_all('div[data-e2e="challenge-item"]')
                
                for el in video_elements[:max_results]:
                    link_el = await el.query_selector('a')
                    views_el = await el.query_selector('strong[data-e2e="video-views"]')
                    desc_el = await el.query_selector('div[data-e2e="challenge-item-desc"]')
                    
                    if link_el and views_el:
                        link = await link_el.get_attribute('href')
                        views_text = await views_el.inner_text()
                        desc = await desc_el.inner_text() if desc_el else "Pas de description"
                        
                        results.append({
                            "url": link,
                            "views": views_text,
                            "description": desc
                        })
                        
            except Exception as e:
                print(f"[TrendScraper] Erreur lors du scraping : {e}")
                
            finally:
                await browser.close()
                
        return results

    def analyze_trends(self, scraped_data):
        """
        Filtre les vidéos en fonction des vues pour détecter les 'winners'.
        """
        print(f"[TrendScraper] Analyse de {len(scraped_data)} vidéos...")
        winners = []
        for data in scraped_data:
            # Simplification : on cherche les vidéos avec "M" (Millions) ou un gros "K"
            if "M" in data["views"] or ("K" in data["views"] and float(data["views"].replace("K", "")) > 100):
                winners.append(data)
                
        return winners

if __name__ == "__main__":
    # Test local
    async def main():
        scraper = TrendScraper(headless=True)
        # Test avec un hashtag de niche électronique (comme demandé par le Hub)
        data = await scraper.get_trending_videos("cargadgets", max_results=5)
        trends = scraper.analyze_trends(data)
        
        print(f"\n--- TENDANCES DETECTEES ({len(trends)}) ---")
        for t in trends:
            print(f"👁️ Vues: {t['views']} | 🔗 URL: {t['url']} | 📝 Desc: {t['description'][:50]}...")
            
    asyncio.run(main())
