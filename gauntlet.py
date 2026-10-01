import json
import logging
import tempfile
import time
from pathlib import Path

from scrapling.fetchers import DynamicFetcher, Fetcher, StealthyFetcher
from scrapling.parser import Selector

from spiders import BooksSpider

JS_URL = "https://quotes.toscrape.com/js/"
BOOKS_URL = "https://books.toscrape.com/"
PROTECTED_URLS = [
    "https://nopecha.com/demo/cloudflare",
    "https://www.scrapingcourse.com/cloudflare-challenge",
    "https://www.scrapingcourse.com/antibot-challenge",
]
CHALLENGE_TITLE = "Just a moment..."
RESULTS_FILE = Path("output") / "gauntlet.json"


class QuietBooksSpider(BooksSpider):
    logging_level = logging.WARNING


def check(round_name: str, name: str, passed: bool, detail: str) -> dict:
    return {"round": round_name, "check": name, "passed": passed, "detail": detail}


def attempt(fetch, url: str, **options) -> tuple[bool, str]:
    started = time.perf_counter()
    try:
        page = fetch(url, **options)
    except Exception as error:
        return False, f"{type(error).__name__} after {time.perf_counter() - started:.1f}s"
    title = (page.css("title::text").get() or "").strip()
    got_through = page.status == 200 and title != CHALLENGE_TITLE
    return got_through, f"HTTP {page.status} in {time.perf_counter() - started:.1f}s"


def speed_round() -> list[dict]:
    result = QuietBooksSpider().start()
    stats = result.stats
    unique_books = len({item["upc"] for item in result.items})
    return [
        check(
            "speed",
            "crawl 1000 book pages",
            unique_books == 1000 and stats.failed_requests_count == 0,
            f"{unique_books} unique books, {stats.requests_count} requests in "
            f"{stats.elapsed_seconds:.1f}s ({stats.requests_per_second:.1f} req/s), "
            f"{stats.failed_requests_count} failed",
        )
    ]


def javascript_round() -> list[dict]:
    started = time.perf_counter()
    plain = len(Fetcher.get(JS_URL).css(".quote"))
    plain_seconds = time.perf_counter() - started

    started = time.perf_counter()
    rendered = len(DynamicFetcher.fetch(JS_URL, wait_selector=".quote").css(".quote"))
    rendered_seconds = time.perf_counter() - started

    return [
        check(
            "javascript",
            "render a JS-only page",
            plain == 0 and rendered == 10,
            f"Fetcher saw {plain} quotes in {plain_seconds:.1f}s, "
            f"DynamicFetcher saw {rendered} in {rendered_seconds:.1f}s",
        )
    ]


def antibot_round() -> list[dict]:
    checks = []
    for url in PROTECTED_URLS:
        _, plain = attempt(Fetcher.get, url)
        _, browser = attempt(DynamicFetcher.fetch, url)
        passed, stealth = attempt(StealthyFetcher.fetch, url, solve_cloudflare=True)
        checks.append(
            check(
                "antibot",
                url,
                passed,
                f"Fetcher {plain} | DynamicFetcher {browser} | StealthyFetcher {stealth}",
            )
        )
    return checks


def adaptive_round() -> list[dict]:
    selector = "article.product_pod .price_color"
    html = Fetcher.get(BOOKS_URL).html_content
    storage = {
        "storage_file": str(Path(tempfile.mkdtemp()) / "adaptive.db"),
        "url": BOOKS_URL,
    }

    original = Selector(html, url=BOOKS_URL, adaptive=True, storage_args=storage)
    expected = original.css(selector, identifier="first_price", auto_save=True)[0].text

    redesigned_html = (
        html.replace("product_pod", "card-x9")
        .replace("price_color", "amt")
        .replace("product_price", "buy-box")
        .replace('<article class="card-x9">', '<section class="wrap"><article class="card-x9">')
        .replace("</article>", "</article></section>")
    )
    redesigned = Selector(redesigned_html, url=BOOKS_URL, adaptive=True, storage_args=storage)
    broken = len(redesigned.css(selector))
    relocated = redesigned.css(selector, identifier="first_price", adaptive=True)
    found = relocated[0].text if relocated else None

    return [
        check(
            "adaptive",
            "survive a site redesign",
            broken == 0 and found == expected,
            f"old selector matched {broken} elements after the redesign, "
            f"adaptive mode recovered {found!r} (expected {expected!r})",
        )
    ]


def main() -> None:
    logging.getLogger("scrapling").setLevel(logging.WARNING)

    checks = []
    for run_round in (speed_round, javascript_round, antibot_round, adaptive_round):
        print(f"Running {run_round.__name__.replace('_', ' ')}...", flush=True)
        checks.extend(run_round())

    print()
    for item in checks:
        verdict = "PASS" if item["passed"] else "FAIL"
        print(f"[{verdict}] {item['round']:<10} {item['check']}")
        print(f"       {item['detail']}")

    passed = sum(item["passed"] for item in checks)
    print(f"\n{passed}/{len(checks)} checks passed")

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps(checks, indent=2, ensure_ascii=False))
    print(f"Results saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
