import asyncio
import pandas as pd

from scraper.utils.crawlers.products_scraper import ProductsGridScraper
from scraper.utils.crawlers.details_scraper import ProductDetailsScraper
from scraper.utils.procesing.transformer import products_to_df, details_to_df
from scraper.utils.config.settings import load_config_json

async def main():
    config = load_config_json()

    use_proxy = config["SITE"]["USE_PROXY"]
    base_url = config["SITE"]["BASE_URL"]
    products_per_page = config["SITE"]["PRODUCTS_PER_PAGE"]

    scraper = ProductsGridScraper(use_proxy=use_proxy)
    products = await scraper.scrape_products(base_url, products_per_page)
    df = products_to_df(products)

    products_details = []
    for _, row in df.head(5).iterrows():
        url = row["url"]
        scraper = ProductDetailsScraper()
        product_info = await scraper.scrape_product_details(url)
        products_details.append(product_info)

    details_to_df(products_details)

if __name__ == "__main__":
    asyncio.run(main())
