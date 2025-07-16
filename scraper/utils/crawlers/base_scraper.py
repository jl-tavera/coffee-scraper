from playwright.async_api import async_playwright
from scraper.utils.connection.proxy import get_proxies
from scraper.utils.connection.config import load_env_variables, load_config

class BaseScraper:
    def __init__(self):
        self.config = load_config()
        self.env = load_env_variables()
        self.headers, self.proxy, _ = get_proxies(self.env, self.config)
        self.browser = None
        self.context = None
        self.page = None


    async def setup(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent=self.headers["User-Agent"],
            proxy=self.proxy,
            extra_http_headers=self.headers,
            ignore_https_errors=True
        )
        self.page = await self.context.new_page()

    async def go_to(self, url):
        await self.page.goto(url)

    async def close(self):
        await self.browser.close()

