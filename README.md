# scrapling-web-crawlers

Web crawlers built on [Scrapling](https://github.com/D4Vinci/Scrapling). Each spider lives in `spiders/` and is run through one command-line entry point, `main.py`, which exports the scraped items to JSON, JSONL, CSV or XML.

## Requirements

- Python 3.10 or newer

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The spiders use plain HTTP requests and need nothing else. The gauntlet uses Scrapling's browser-based fetchers (`DynamicFetcher`, `StealthyFetcher`), so download the browsers once with:

```bash
scrapling install
```

## Usage

```bash
python main.py quotes
python main.py quotes -o output/quotes.csv
python main.py quotes --crawldir .crawl/quotes
```

The first writes `output/quotes.json`, the second picks CSV from the file extension, and the third runs a checkpointed crawl that can be paused and resumed.

| Option | Meaning |
|---|---|
| `spider` | Name of the spider to run (see below) |
| `-o`, `--output` | Output file: `.json`, `.jsonl`, `.csv` or `.xml`. Default is `output/<spider>.json` |
| `--crawldir` | Directory for crawl checkpoints. Press Ctrl+C to pause, then run the same command again to resume |

## Spiders

| Name | Site | Fields |
|---|---|---|
| `quotes` | [quotes.toscrape.com](https://quotes.toscrape.com/) | `text`, `author`, `tags` |
| `books` | [books.toscrape.com](https://books.toscrape.com/) | `title`, `category`, `price`, `rating`, `in_stock`, `upc`, `url` |

Both sites are practice targets built for scraping. `quotes` walks 10 listing pages; `books` walks 50 listing pages and opens all 1000 book detail pages.

Example `books` item:

```json
{
  "title": "A Light in the Attic",
  "category": "Poetry",
  "price": 51.77,
  "rating": 3,
  "in_stock": 22,
  "upc": "a897fe39b1053632",
  "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
}
```

## Gauntlet

`gauntlet.py` puts Scrapling through four rounds against public practice targets and prints a pass/fail scorecard. Results are also written to `output/gauntlet.json`.

```bash
python gauntlet.py
```

| Round | What it checks |
|---|---|
| speed | Crawls all 1000 book pages with the `books` spider and reports requests per second and failures |
| javascript | Loads a page whose content only exists after JavaScript runs, with `Fetcher` and with `DynamicFetcher` |
| antibot | Sends all three fetchers at three Cloudflare-protected demo pages and records which get through |
| adaptive | Saves an element, rewrites the page's class names and structure, then asks Scrapling to find the element again |

Results from a run on 2026-10-01 (Scrapling 0.4.15, macOS, home connection):

| Round | Result |
|---|---|
| speed | 1000 unique books, 1050 requests in 40.7s (25.8 requests/second), 0 failed |
| javascript | `Fetcher` saw 0 quotes, `DynamicFetcher` saw all 10 in 3.7s |
| antibot | `Fetcher` and `DynamicFetcher` got HTTP 403 on all three pages; `StealthyFetcher` got HTTP 200 on all three, in 5 to 15 seconds each |
| adaptive | The old selector matched nothing after the redesign; adaptive mode recovered the same price element |

The antibot targets are demo pages published for testing scrapers: [nopecha.com/demo/cloudflare](https://nopecha.com/demo/cloudflare) and the ScrapingCourse [Cloudflare](https://www.scrapingcourse.com/cloudflare-challenge) and [antibot](https://www.scrapingcourse.com/antibot-challenge) challenges. Timings vary between runs.

## Adding a spider

1. Create `spiders/<name>.py` with a `Spider` subclass. Set `name` and `start_urls`, and write an async `parse` that yields dicts for items and `response.follow(...)` for links to crawl next. `spiders/quotes.py` is a working example.
2. Add the class to the tuple in `spiders/__init__.py`.

It is then available as `python main.py <name>`.

## Project layout

```
main.py            command-line entry point for spiders
gauntlet.py        four-round test of what Scrapling can do
spiders/
  __init__.py      registry of available spiders
  quotes.py        quotes.toscrape.com spider
  books.py         books.toscrape.com spider
requirements.txt   pinned dependencies
output/            example results from real runs of the spiders and the gauntlet
```

## Responsible use

Check a site's terms of service and `robots.txt` before crawling it, and keep `concurrent_requests` low enough that you are not hammering the server.

## License

Apache License 2.0. See [LICENSE](LICENSE).
