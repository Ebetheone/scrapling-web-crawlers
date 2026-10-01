from scrapling.spiders import Response, Spider


class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 5

    async def parse(self, response: Response):
        for quote in response.css(".quote"):
            yield {
                "text": quote.css(".text::text").get(),
                "author": quote.css(".author::text").get(),
                "tags": quote.css(".tag::text").getall(),
            }

        next_page = response.css(".next a")
        if next_page:
            yield response.follow(next_page[0].attrib["href"])
