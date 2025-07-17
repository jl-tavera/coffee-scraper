# Coffee Scraper

## Table of Contents

- [File Structure](#file-structure)
- [Scraping Stack](#scraping-stack)
- [Scraping Logic](#scraping-logic)
  - [Product Grid](#product-grid)
  - [Product Price](#product-price)
  - [Individual Page](#individual-page)
- [Future Recommendations](#future-recommendations)
  - [Database](#database)
  - [Celery and Redis](#celery-and-redis)
  - [Monitoring and Logging](#monitoring-and-logging)
  - [Testing and CI/CD](#testing-and-cicd)


## File Structure


- `.venv/`: Local Python virtual environment folder (should be excluded from Git).
- `assets/images/`: Optional folder to store scraped images or documentation screenshots.
- `assets/user_agents/user_agents.csv`: Contains multiple user-agent strings for header rotation.
- `scraper/`: Root scraping package.
  - `__init__.py`: Declares this as a Python package.
  - `config.json`: Stores all site-specific settings and locators, separated by functionality.
  - `main.py`: Async entry point. Calls the grid scraper, then scrapes the detail pages and saves both datasets.
  - `utils/`: Contains all organized modules:
    - `config/`: Configuration logic
      - `config.py`: Loads values from `config.json` and makes them accessible to other modules.
      - `settings.py`: Stores static constants like default headers or environment toggles.
    - `crawlers/`: Contains all classes that perform actual scraping
      - `base_scraper.py`: Base scraper that handles Playwright setup, proxy rotation, and browser configuration.
      - `products_scraper.py`: Scrapes paginated product cards (grid view).
      - `details_scraper.py`: Scrapes the full product detail pages.
      - `url_manager.py`: Utility to construct paginated URLs dynamically.
    - `processing/`: Handles data cleaning and transformation
      - `transformer.py`: Cleans and structures raw scraped data into pandas DataFrames and CSVs.
- `.gitignore`: Prevents committing `__pycache__`, `.venv/`, and other temporary files.
- `README.md`: Documentation for how the scraper works (this file).
- `requirements.txt`: List of Python packages required to run the project.

## Scraping Stack

I decided to use Playwright because it has many advantages like full JavaScript rendering, fast headless operation, and more control over mouse/keyboard events compared to traditional scrapers. I could have used Scrapy—which is better suited for static HTML websites—but since there is JavaScript logic on the site, Playwright is a better fit.

To rotate proxies and avoid blocking, I integrated BrightData. This gives the advantage of managing residential IPs, and lets me scale more safely if I want to schedule this scraper or run it across large batches of URLs.

Additionally, I used a modular structure with Python classes for flexibility and scalability. All the scraping logic is divided per responsibility (grid, product page, transformation), and all locators are managed from a centralized `config.json` file, so changes to the website structure don’t require touching the logic code.


## Scraping Logic

### Product Grid

From the original instructions, I know that I need to scrape all the product data from the Brew: All Coffee section. My mission, according to the instructions, is to first: write a Python script that saves all the products with their URL, title, and price, but we are going to get more information including: the brand, the badges (Free Shipping, Subscription, Recommended, On Sale, etc.), and the Sale Price if it exists.

First, we need to target the grid of products in the section, as we can see in the screenshot below:

![Grid Screenshot](./assets/images/grid_screenshot.png)

The `div` has a class of `productGrid`, which is not a sign of any kind of dynamic class, and after further inspection, it's the only `productGrid` on the webpage, so we can safely target this grid. But we need to target the grid for all the pages.

Above the grid, inside the page, there is a *Products Per Page* controller that has a default value of 12. Let’s see how simple it is to change this product filter. Why do we want to change this product filter, you may ask? If we change the product filter to a larger size, we can make fewer requests to the webpage. For this simple exercise, it doesn’t really matter, but for a production-level scraper, fewer requests are better (in most cases). Sometimes there may be some disadvantages to this, like increased page load time or risk of hitting size/time limits on the server response, but in this case, which has no lazy scroll loading, I think it’s good to use the largest products-per-page value available. When we change to the largest, we see the URL change from:

https://prima-coffee.com/brew/coffee

to

https://prima-coffee.com/brew/coffee?products.size=100

—indicating we can control filters through the URL. In some webpages, this is not the case—there can exist dynamic URLs, where filters are applied client-side using JavaScript and do not reflect in the URL, making it harder to scrape without a headless browser. But let’s take advantage of the URL logic here.

Next, we need to make sure we’re scraping all the products, not just the first page, so we need to target all the pages. At the moment, there are only 194 items, so let’s go back to our default 12 items per page to analyze this in more detail. When we click on the second page or "Next", we see the URL change to:

https://prima-coffee.com/brew/coffee?products.from=12

If we click "Next" or the third page, we go to the link:

https://prima-coffee.com/brew/coffee?products.from=24

As you can see, the URL changes according to this formula:

https://prima-coffee.com/brew/coffee?products.from={products_per_page * previous_page}

If we go to a webpage out of range, we see an empty grid, as shown below:

![Empty Grid Screenshot](./assets/images/empty_grid_screenshot.png)

At the same time, if we analyze the pagination, we see on the left the total number of items, and a page navigator that shows the first results, three dots, and the last page. There’s a "Next" button that takes us to the next page. When we reach the final page, this button disappears, and we only have the "Previous" button. So to scrape all the items, we have the following options:

1. Use the total item count to calculate the number of pages (integer division of total items by items per page). In this case: 194 items, so we have `194 // 100 = 1`, meaning we only visit the initial page and the one with `products.from=100`.

2. Visit pages until there is no "Next" button—so we visit the first page, then `products.from=100`, then `products.from=200`.

3. Visit pages until the grid is empty—same as above: first page, `products.from=100`, and then `products.from=200`.

There may be more options, but I think these are the three most efficient. Nonetheless, option one and two depend heavily on the style of the pagination navigator, which can change with any redesign. An empty grid is more tied to the webpage’s internal logic, so although option one gives a more concise limit, option three is the best way to go to not make more requests than you need. 

Finally, before planning the code, let’s decide on the information to scrape. In the following screenshot, you have an example of a product. I made a diagram that shows all the info that appears in the product card:

![Product Diagram](./assets/images/product_diagram.png)

This corresponds to: title, price, brand, badges, sale price (if it exists), image URL, and product URL. Also, in the diagram, you can find the classes of each element, which again appear not to be dynamic, so we can use them to target the elements. Obviously, there are product cards that don’t have a sale price or badges, but I think this is very important information you want to take into account when web scraping.

To scrape all of this, I created a class called `ProductsGridScraper`. This class inherits from the previously defined `BaseScraper` and is structured in a modular way. It leverages a JSON-based locator configuration to extract the relevant product data, which keeps the logic clean and easily adaptable. The core scraping loop lives inside the `scrape_products` method, which handles pagination using a custom `URLManager`. The actual data extraction happens in the `_scrape_current_page` method, where each product card is parsed using the defined locators. The scraper extracts the following elements:

- `title`: the product title  
- `price`: the standard price  
- `url`: the link to the product’s detail page  
- `brand`: the brand name  
- `badges`: a list of any promotional badges (e.g., “Staff Pick”)  
- `sale_price`: the discounted price, if available  
- `image`: the image URL  

Each key is extracted using conditional checks to avoid breaking the scraper if some elements are missing. This makes the scraper robust, easy to test, and simple to extend or debug.


### Product Price

My second mission is to enable filter and sorting by price so the coffee shop owners can easily decide which equipment fits their budget. There are two ways you can filter by price:

1. Pre-scraping filtering: Use the webpage’s filters (in this case, URL filters) to filter the prices. This can reduce the amount of pages to scrape, and with that, the number of requests.
2. Post-scraping filtering: After scraping all the products, filter the ones in the price range (this may be with a SQL query). Although this can result in more requests, it doesn’t depend on the webpage’s filter logic. If that logic changes, the filter breaks.

I'm going to explain how to implement the first option, but option two is the one I would implement.

To analyze how the filters work, it depends a lot on the webpage. Some webpages use JavaScript to filter, and this cannot be accessed through the URL because the filter is applied client-side, and the server receives no query parameter indicating the filtering—so the HTML returned remains the same. Fortunately, this is not our case. For example, let’s see what happens when we set a price range from 100 to 1000. As you can see, the URL is:

https://prima-coffee.com/brew/coffee?products.filter.0.not.0.all.0.field=availability&products.filter.0.not.0.all.0.value.0=OutOfStock&products.filter.0.not.0.all.1.field=categories&products.filter.0.not.0.all.1.value.0=Deals&products.filter.1.field=price&products.filter.1.range.0.gte=100&products.filter.1.range.0.lte=1000

In the last part, you can see there’s a:

products.filter.1.range.0.gte=100
products.filter.1.range.0.lte=1000


This way, you can modify the values to any price range you want. Obviously, this affects the total amount of items. To go to all the pages, let’s see what happens when we go to the next page:

https://prima-coffee.com/brew/coffee?products.filter.0.not.0.all.0.field=availability&products.filter.0.not.0.all.0.value.0=OutOfStock&products.filter.0.not.0.all.1.field=categories&products.filter.0.not.0.all.1.value.0=Deals&products.filter.1.field=price&products.filter.1.range.0.gte=100&products.filter.1.range.0.lte=1000&products.from=12

Now, at the end, we have the same pagination parameter `&products.from=12`, so we can apply any of the methods we previously mentioned.

Sorting works in a similar way. The webpage allows sorting by price through a URL parameter, but you can also handle sorting yourself after scraping all products—especially if you plan to store them in a database or manipulate them with Python or SQL.

### Individual Page

Finally, my third mission is to, based on the first 5 cheapest items, scrape all the information available including images, upc, sku, etc.

For this, we already have from the previous exercise the prices and the URLs of the products so we can find the cheapest ones.

When we head to an individual page, we see there are the following sections:

1. Product Carousel Images: Images of the product  
2. Product Details: Brand, title, number of reviews, price, sku, mpn, condition, current stock  
3. Product Description: It has two parts—description and specification  
4. Product Specifications: Some products have another tab of additional information  
5. Reviews Section: Some products have a reviews section; I just want to extract the review summary  
6. Q&A Section: I want to get the questions and answers of the products  

For this, I created a class called `ProductDetailsScraper` that also inherits from the `BaseScraper`, and each of the sections is extracted using separate modular methods. The entire process is encapsulated inside the method `scrape_product_details`, which takes a `product_url` and returns a detailed dictionary of product attributes. Each field is handled gracefully in case the element is missing.

These are the internal methods responsible for each section:

- `_extract_images`: scrapes all image URLs from the carousel by querying anchor `href` attributes  
- `_extract_product_info`: gets brand, title, price, and a dynamic dictionary of attributes like SKU, UPC, MPN, and condition from the `<dt>`/`<dd>` pairs  
- `_extract_stock_info`: pulls stock availability if present  
- `_extract_description`: walks through each tag (like paragraphs or list items) inside the description container and concatenates their text  
- `_extract_specifications`: parses tables row-by-row to build a dictionary of specs  
- `_extract_review_summary`: gets both the numeric score and total review count (if available)  
- `_extract_questions_and_answers`: loops through question containers, collects question metadata and the associated list of answers  

Each method uses locators defined in the JSON-based config under the `PRODUCT_DETAILS_LOCATORS` key and follows conditional patterns to prevent the scraper from failing due to missing DOM elements. The final return is a single structured dictionary with keys like `brand`, `title`, `price`, `images`, `description`, `specifications`, `reviews`, `questions`, and `stock`. Everything is structured to be testable, debuggable, and easy to extend.



## Future Recommendations

If you want to create a robust production-ready scraper that is scheduled to work every couple of hours, I want to make some recommendations of what is possible.

### Database

Create a good database schema to prevent deduplication, avoid saving the same product multiple times, and store changes in price instead of rewriting everything. Use a relational database like PostgreSQL where you can save product data, store historical prices in a separate table, and save nested objects (like reviews or questions) using JSON fields. Also, define indexes on relevant fields (like SKU, price, or brand) to speed up queries.

### Celery and Redis

With Celery and Redis you can add better workers for background tasks. This allows you to schedule scraping jobs, queue the detail scraping separately from the grid scraping, and retry failed tasks without blocking the whole process. Redis serves as the message broker, and Celery makes it easier to scale horizontally and handle multiple jobs concurrently.

### Monitoiring and Logging

You can add Prometheus to collect metrics like job duration, number of items scraped, or error rates. Then, connect that with Grafana to visualize those metrics in real time and track the health of your scraper. Also, improve your logging by adding structured logs so you can trace issues faster and understand what part of the scraper failed when something goes wrong.

### Testing and CI/CD

You can add unit tests for the transformers, parsing functions, and the logic that loads your configuration. Use GitHub Actions to run those tests automatically on every push or pull request. You could also schedule scraping jobs to run daily using GitHub Actions with a cron job. If needed, consider integration testing to check whether your locators are still working when the site changes.




