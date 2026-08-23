import argparse
from pathlib import Path

from yelp_service import search_live_businesses


DEFAULT_OUTPUT = Path("data/export.csv")


def prompt_if_missing(value, message):
    if value:
        return value
    return input(message).strip()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Search Yelp businesses by city and export the results to CSV."
    )
    parser.add_argument("--term", help="Search term or category, such as Restaurants")
    parser.add_argument("--location", help="City and state, such as New York City, NY")
    parser.add_argument(
        "--pages",
        type=int,
        default=None,
        help="Number of 50-result pages to fetch",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="CSV output path",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print(
        "Welcome to the Yelp Search Program.\n"
        "Search Yelp by term and city, then export listings to CSV.\n"
    )

    term = prompt_if_missing(
        args.term,
        "What category or term would you like to search for? e.g. Restaurants\n",
    )
    location = prompt_if_missing(
        args.location,
        "What city and state are you searching? e.g. New York City, NY\n",
    )
    pages = args.pages
    if pages is None:
        pages = int(input("How many 50-result pages should be fetched?\n").strip())

    if pages < 1:
        raise SystemExit("Pages must be 1 or higher.")

    try:
        business_df = search_live_businesses(term, location, pages=pages)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    args.output.parent.mkdir(parents=True, exist_ok=True)
    business_df.to_csv(args.output, index=False)
    print(f"Exported {len(business_df)} businesses to {args.output}")


if __name__ == "__main__":
    main()
