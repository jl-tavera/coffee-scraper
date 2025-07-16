from scraper.utils.crawlers.base_scraper import BaseScraper
from scraper.utils.crawlers.url_manager import URLManager
from scraper.utils.procesing.procesing import *

class ProductsGridScraper(BaseScraper):

    async def scrape_products(self, base_url: str, products_per_page: int = 100) -> list[dict]:
        await self.setup()
        all_products = []

        url_manager = URLManager(base_url, products_per_page)

        # Visit first page
        first_url = f"{base_url}?products.size={products_per_page}"
        await self.go_to(first_url)

        # Extract total items
        total_text = await self.page.locator(".pagination-info").first.text_content()
        total_items = get_total_items(total_text)

        # Scrape first page
        products = await self._scrape_current_page(base_url)
        all_products.extend(products)

        # Generate and scrape remaining pages
        remaining_urls = url_manager.get_remaining_urls(total_items)
        for url in remaining_urls:
            await self.go_to(url)
            products = await self._scrape_current_page(base_url)
            all_products.extend(products)

        await self.close()
        return all_products

    async def _scrape_current_page(self, base_url: str) -> list[dict]:
        items = await self.page.locator("a.product.ng-scope.relative").all()
        products = []

        for item in items:
            product = {
                "title": await item.locator("h4.card-title").text_content() if await item.locator("h4.card-title").count() > 0 else None,
                "price": await item.locator(".price-section .price--main").text_content() if await item.locator(".price-section .price--main").count() > 0 else None,
                "url": await item.get_attribute("href"),
                "brand": await item.locator("p.card-text.card-text--brand").text_content() if await item.locator("p.card-text.card-text--brand").count() > 0 else None,
                "badges": [
                    await badge.text_content()
                    for badge in await item.locator(".badges-container .badge").all()
                ],
                "sale_price": await item.locator("span[data-product-rrp-price-without-tax]").text_content()
                if await item.locator("span[data-product-rrp-price-without-tax]").count() > 0
                else None,
                "image": await item.locator("img").get_attribute("src") if await item.locator("img").count() > 0 else None,
            }

            print(f"🔎 Scraped: {product['title']}")
            products.append(product)

        return products
