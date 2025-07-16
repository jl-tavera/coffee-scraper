
class URLManager:
    def __init__(self, base_url: str, products_per_page: int = 100):
        self.base_url = base_url
        self.products_per_page = products_per_page

    def get_remaining_urls(self, total_items: int) -> list[str]:
 
        urls = []
        for offset in range(self.products_per_page, total_items, self.products_per_page):
            url = f"{self.base_url}?products.size={self.products_per_page}&products.from={offset}"
            urls.append(url)
        return urls

