import argparse
from pathlib import Path

from spiders import SPIDERS

EXPORTERS = {".json": "to_json", ".jsonl": "to_jsonl", ".csv": "to_csv", ".xml": "to_xml"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Scrapling spider and export its items.")
    parser.add_argument("spider", choices=sorted(SPIDERS), help="which spider to run")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=f"output file, format picked by extension ({', '.join(EXPORTERS)}); default: output/<spider>.json",
    )
    parser.add_argument(
        "--crawldir",
        type=Path,
        help="directory for crawl checkpoints; pass the same one again to resume a paused crawl",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = Path("output") / f"{args.spider}.json"
    if args.output.suffix not in EXPORTERS:
        parser.error(f"unsupported output format '{args.output.suffix}', use one of: {', '.join(EXPORTERS)}")
    return args


def main() -> None:
    args = parse_args()

    result = SPIDERS[args.spider](crawldir=args.crawldir).start()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    getattr(result.items, EXPORTERS[args.output.suffix])(args.output)

    status = "paused" if result.paused else "finished"
    print(f"\nCrawl {status}: {len(result.items)} items -> {args.output}")
    if result.paused:
        print(f"Run the same command again to resume from {args.crawldir}")


if __name__ == "__main__":
    main()
