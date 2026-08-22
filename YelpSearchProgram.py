import argparse
import os
from pathlib import Path

import pandas as pd
import requests


YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
DEFAULT_OUTPUT = Path("data/export.csv")
PAGE_SIZE = 50
OUTPUT_COLUMNS = [
    "Business",
    "Business ID",
    "City",
    "State",
    "Category",
    "Latitude",
    "Longitude",
    "Price",
    "Reviews",
    "Rating",
]


def get_api_key():
    env_api_key = os.getenv("YELP_API_KEY")
    if env_api_key:
        return env_api_key

    try:
        from config import api_key
    except ImportError as exc:
        raise SystemExit(
            "Missing Yelp API key. Set YELP_API_KEY or copy config.example.py "
            "to config.py and set api_key."
        ) from exc

    if not api_key or api_key == "replace-with-your-yelp-api-key":
        raise SystemExit("Set YELP_API_KEY or set api_key in config.py before running.")

    return api_key


def prompt_if_missing(value, message):
    if value:
        return value
    return input(message).strip()


def fetch_yelp_page(term, location, offset):
    headers = {"Authorization": f"Bearer {get_api_key()}"}
    params = {
        "term": term,
        "location": location,
        "offset": offset,
        "limit": PAGE_SIZE,
    }
    response = requests.get(YELP_SEARCH_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def normalize_price(price):
    if not price:
        return 0
    return len(price)


def business_to_row(business):
    categories = business.get("categories") or [{}]
    coordinates = business.get("coordinates") or {}
    location = business.get("location") or {}

    return {
        "Business": business.get("name"),
        "Business ID": business.get("id"),
        "City": location.get("city"),
        "State": location.get("state"),
        "Category": categories[0].get("title"),
        "Latitude": coordinates.get("latitude"),
        "Longitude": coordinates.get("longitude"),
        "Price": normalize_price(business.get("price")),
        "Reviews": business.get("review_count"),
        "Rating": business.get("rating"),
    }


def search_businesses(term, location, pages):
    rows = []

    for page in range(pages):
        offset = page * PAGE_SIZE
        payload = fetch_yelp_page(term, location, offset)
        businesses = payload.get("businesses", [])

        if not businesses:
            break

        rows.extend(business_to_row(business) for business in businesses)

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Search Yelp businesses and export the results to CSV."
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
        "Search Yelp by term and location, then export listings to CSV.\n"
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

    business_df = search_businesses(term, location, pages)
    business_df = business_df.drop_duplicates(subset=["Business ID"])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    business_df.to_csv(args.output, index=False)
    print(f"Exported {len(business_df)} businesses to {args.output}")


if __name__ == "__main__":
    main()
