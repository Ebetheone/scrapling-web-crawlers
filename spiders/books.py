import re

from scrapling.spiders import Response, Spider

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BooksSpider(Spider):
    name = "books"
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]
    concurrent_requests = 16

    async def parse(self, response: Response):
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(href, callback=self.parse_book)

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page)

    async def parse_book(self, response: Response):
        details = dict(
            zip(
                response.css("table.table th::text").getall(),
                response.css("table.table td::text").getall(),
            )
        )
        rating_word = response.css("p.star-rating::attr(class)").get().split()[-1]

        yield {
            "title": response.css("h1::text").get(),
            "category": response.css("ul.breadcrumb li:nth-child(3) a::text").get(),
            "price": float(response.css("p.price_color::text").re_first(r"[\d.]+")),
            "rating": RATINGS[rating_word],
            "in_stock": int(re.search(r"\d+", details["Availability"]).group()),
            "upc": details.get("UPC"),
            "url": response.url,
        }
