import asyncio
import pandas as pd
import os

from scraper.utils.connection.proxy import proxy_dicts

from scraper.utils.crawlers.products_scraper import ProductsGridScraper
from scraper.utils.connection.config import load_config

async def main():
    # Load config
    config = load_config()
    # Base URL and settings
    base_url = config["SITE"]["BASE_URL"]
    products_per_page = config["SITE"]["PRODUCTS_PER_PAGE"]

    # Run scraper
    print(f"🔍 Scraping products from: {base_url}")
    scraper = ProductsGridScraper()
    products = await scraper.scrape_products(base_url, products_per_page)

    # Save to CSV
    df = pd.DataFrame(products)
    df.to_csv("prima_products.csv", index=False)
    print(f"✅ Done! Scraped {len(df)} products and saved to 'prima_products.csv'.")

if __name__ == "__main__":
    asyncio.run(main())
