from spiders.books import BooksSpider
from spiders.quotes import QuotesSpider

SPIDERS = {spider.name: spider for spider in (BooksSpider, QuotesSpider)}
