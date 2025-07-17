import asyncio
import pandas as pd

from scraper.utils.crawlers.products_scraper import ProductsGridScraper
from scraper.utils.crawlers.details_scraper import ProductDetailsScraper
from scraper.utils.config.settings import load_config_json

async def main():
    # Load config
    config = load_config_json()
    # Base URL and settings
    use_proxy = config["SITE"]["USE_PROXY"]
    base_url = config["SITE"]["BASE_URL"]
    products_per_page = config["SITE"]["PRODUCTS_PER_PAGE"]

    # Run scraper
    # scraper = ProductsGridScraper(use_proxy=use_proxy)
    # products = await scraper.scrape_products(base_url, products_per_page)

    # # Save to CSV
    # df = pd.DataFrame(products)
    # df.to_csv("prima_products.csv", index=False)
    # print(f"Done! Scraped {len(df)} products and saved to 'prima_products.csv'.")

    url = "https://prima-coffee.com/equipment/hario/vcf-02-40m-hario-sp"
    scraper = ProductDetailsScraper()
    product_info = await scraper.scrape_product_details(url)
    print(product_info)

if __name__ == "__main__":
    asyncio.run(main())
