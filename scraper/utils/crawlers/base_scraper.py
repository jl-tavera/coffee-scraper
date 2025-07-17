from playwright.async_api import async_playwright
from scraper.utils.connection.proxy import get_proxies
from scraper.utils.connection.config import load_env_variables, load_config

class BaseScraper:
    def __init__(self, use_proxy: bool = True):
        self.config = load_config()
        self.env = load_env_variables()
        self.use_proxy = use_proxy

        self.headers = {}
        self.proxy = None

        if self.use_proxy:
            self.headers, self.proxy, _ = get_proxies(self.env, self.config)

        self.browser = None
        self.context = None
        self.page = None

    async def setup(self):
        playwright = await async_playwright().start()
        launch_args = {"headless": True}
        context_args = {
            "user_agent": self.headers.get("User-Agent"),
            "extra_http_headers": self.headers,
            "ignore_https_errors": True
        }

        if self.use_proxy:
            context_args["proxy"] = self.proxy

        self.browser = await playwright.chromium.launch(**launch_args)
        self.context = await self.browser.new_context(**context_args)
        self.page = await self.context.new_page()

    async def go_to(self, url):
        await self.page.goto(url)
        print(f"Loaded page: {await self.page.title()}")

    async def close(self):
        await self.browser.close()


