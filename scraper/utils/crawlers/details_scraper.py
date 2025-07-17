from scraper.utils.crawlers.base_scraper import BaseScraper
import re


class ProductDetailsScraper(BaseScraper):
    def __init__(self, use_proxy: bool = True):
        super().__init__(use_proxy)
        self.locators = self.config["PRODUCT_DETAILS_LOCATORS"]

    async def scrape_product_details(self, product_url: str) -> dict:
        await self.setup()
        await self.go_to(product_url)

        images = await self._extract_images()
        info = await self._extract_product_info()
        stock = await self._extract_stock_info()
        description = await self._extract_description()
        specifications = await self._extract_specifications()
        reviews = await self._extract_review_summary()
        questions = await self._extract_questions_and_answers()

        await self.close()

        return {
            **info,
            "images": images,
            "stock": stock,
            "description": description,
            "specifications": specifications,
            "reviews": reviews,
            "questions": questions,
        }

    async def _extract_images(self) -> list[str]:
        selector = self.locators["IMAGES"]["ITEM"]
        image_elements = await self.page.locator(selector).all()
        return [
            await a.get_attribute("href")
            for a in image_elements
            if await a.get_attribute("href") is not None
        ]

    async def _extract_product_info(self) -> dict:
        loc = self.locators["PRODUCT_INFO"]
        brand = await self.page.locator(loc["BRAND"]).text_content()
        title = await self.page.locator(loc["TITLE"]).text_content()
        price = await self.page.locator(loc["PRICE"]).text_content()

        dt_elements = await self.page.locator(loc["DETAILS_DT"]).all()
        dd_elements = await self.page.locator(loc["DETAILS_DD"]).all()

        details = {}
        for dt, dd in zip(dt_elements, dd_elements):
            key = await dt.text_content()
            value = await dd.text_content()
            details[key.strip().rstrip(":")] = value.strip()

        return {
            "brand": brand.strip() if brand else None,
            "title": title.strip() if title else None,
            "price": price.strip() if price else None,
            "details": details,
        }

    async def _extract_stock_info(self) -> str | None:
        stock_locator = self.page.locator(self.locators["STOCK"]["QUANTITY"])
        if await stock_locator.count() > 0:
            stock = await stock_locator.text_content()
            return stock.strip()
        return None

    async def _extract_description(self) -> str:
        selector = self.locators["DESCRIPTION"]["CONTAINER"]
        description_container = self.page.locator(selector)
        if await description_container.count() == 0:
            return ""

        tags = self.locators["DESCRIPTION"]["TAGS"]
        parts = []

        for tag in tags:
            elements = description_container.locator(tag)
            count = await elements.count()
            for i in range(count):
                text = await elements.nth(i).inner_text()
                text = text.strip()
                if text:
                    parts.append(f"- {text}" if tag == "li" else text)

        return "\n".join(parts).strip()

    async def _extract_specifications(self) -> dict:
        selector = self.locators["SPECIFICATIONS"]["TABLE"]
        tables = self.page.locator(selector)

        for i in range(await tables.count()):
            table = tables.nth(i)
            rows = table.locator("tr")
            specs = {}

            for j in range(await rows.count()):
                cells = rows.nth(j).locator("th, td")
                if await cells.count() >= 2:
                    key = (await cells.nth(0).inner_text()).strip().rstrip(":")
                    value = (await cells.nth(1).inner_text()).strip()
                    specs[key] = value

            if specs:
                return specs

        return {}

    async def _extract_review_summary(self) -> dict:
        loc = self.locators["REVIEWS"]
        section = self.page.locator(loc["SECTION"])
        if await section.count() == 0:
            return {"score": None, "reviews_count": None}

        score = await section.locator(loc["SCORE"]).text_content() or ""
        text = await section.locator(loc["TEXT"]).text_content() or ""

        return {
            "score": float(score.strip()) if score.strip().replace('.', '', 1).isdigit() else None,
            "reviews_count": int(re.search(r"\d+", text).group()) if re.search(r"\d+", text) else None
        }

    async def _extract_questions_and_answers(self) -> list[dict]:
        loc = self.locators["QUESTIONS"]
        tab = self.page.locator(loc["TAB"])
        if await tab.count() > 0:
            await tab.click()
            await self.page.wait_for_timeout(6000)

        container = self.page.locator(loc["CONTAINER"])
        if await container.count() == 0 or not await container.is_visible():
            return []

        questions = []
        for q in await container.locator(loc["ITEM"]).all():
            name = (await q.locator(loc["NAME"]).text_content() or "").strip()
            date = (await q.locator(loc["DATE"]).text_content() or "").strip()
            question = (await q.locator(loc["QUESTION"]).text_content() or "").strip()
            answers = [
                (await a.text_content()).strip()
                for a in await q.locator(loc["ANSWERS"]).all()
                if await a.text_content()
            ]
            questions.append({"name": name, "date": date,
                             "question": question, "answers": answers})

        return questions
