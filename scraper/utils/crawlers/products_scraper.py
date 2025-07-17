from scraper.utils.crawlers.base_scraper import BaseScraper
from scraper.utils.crawlers.url_manager import URLManager
from scraper.utils.procesing.procesing import *

class ProductsGridScraper(BaseScraper):
    def __init__(self, use_proxy: bool = True):
        super().__init__(use_proxy)
        self.locators = self.config["PRODUCTS_LOCATORS"]

    async def scrape_products(self, base_url: str, products_per_page: int = 100) -> list[dict]:
        await self.setup()
        all_products = []

        first_url = f"{base_url}?products.size={products_per_page}"
        await self.go_to(first_url)

        total_text = await self.page.locator(".pagination-info").first.text_content()
        total_items = get_total_items(total_text)

        # Scrape first page
        products = await self._scrape_current_page()
        all_products.extend(products)
        
        url_manager = URLManager(base_url, products_per_page)
        for url in url_manager.get_remaining_urls(total_items):
            await self.go_to(url)
            products = await self._scrape_current_page()
            all_products.extend(products)

        await self.close()
        return all_products

    async def _scrape_current_page(self) -> list[dict]:
        loc = self.locators
        items = await self.page.locator(loc["ITEM"]).all()
        products = []

        for item in items:
            product = {
                "title": await item.locator(loc["TITLE"]).text_content()
                    if await item.locator(loc["TITLE"]).count() > 0 else None,

                "price": await item.locator(loc["PRICE"]).text_content()
                    if await item.locator(loc["PRICE"]).count() > 0 else None,

                "url": await item.get_attribute(loc["URL_ATTR"]),

                "brand": await item.locator(loc["BRAND"]).text_content()
                    if await item.locator(loc["BRAND"]).count() > 0 else None,

                "badges": [
                    await badge.text_content()
                    for badge in await item.locator(loc["BADGE"]).all()
                ],

                "sale_price": await item.locator(loc["SALE_PRICE"]).text_content()
                    if await item.locator(loc["SALE_PRICE"]).count() > 0 else None,

                "image": await item.locator(loc["IMAGE"]).get_attribute("src")
                    if await item.locator(loc["IMAGE"]).count() > 0 else None,
            }

            print(f"Scraped Item: {product['title']}")
            products.append(product)

        return products


