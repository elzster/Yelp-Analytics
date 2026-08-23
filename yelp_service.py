import os
from pathlib import Path

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
PAGE_SIZE = 50

CITY_DATASETS = {
    "Austin, TX": DATA_DIR / "AustinTX.csv",
    "Chicago, IL": DATA_DIR / "Chicago.csv",
    "New York, NY": DATA_DIR / "NewYork.csv",
    "San Francisco, CA": DATA_DIR / "SanFrancisco.csv",
    "New Brunswick, NJ": DATA_DIR / "New Brunswick, NJ_Burger.csv",
}

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


def get_api_key(required=True):
    env_api_key = os.getenv("YELP_API_KEY")
    if env_api_key:
        return env_api_key

    try:
        from config import api_key
    except ImportError as exc:
        if required:
            raise RuntimeError(
                "Missing Yelp API key. Set YELP_API_KEY or copy "
                "config.example.py to config.py and set api_key."
            ) from exc
        return None

    if not api_key or api_key == "replace-with-your-yelp-api-key":
        if required:
            raise RuntimeError("Set YELP_API_KEY or set api_key in config.py before running.")
        return None

    return api_key


def normalize_price(price):
    if pd.isna(price) or price in ("", "0", 0):
        return 0
    if isinstance(price, str) and price.startswith("$"):
        return len(price)
    try:
        return int(price)
    except (TypeError, ValueError):
        return 0


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


def clean_dataframe(df):
    df = df.copy()
    unnamed_columns = [col for col in df.columns if col.startswith("Unnamed")]
    if unnamed_columns:
        df = df.drop(columns=unnamed_columns)

    for column in OUTPUT_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[OUTPUT_COLUMNS]
    df["Price"] = df["Price"].apply(normalize_price)
    df["Reviews"] = pd.to_numeric(df["Reviews"], errors="coerce").fillna(0).astype(int)
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0.0)
    return df.drop_duplicates(subset=["Business ID"])


def fetch_yelp_page(term, location, offset=0, limit=PAGE_SIZE, sort_by=None):
    headers = {"Authorization": f"Bearer {get_api_key()}"}
    params = {
        "term": term,
        "location": location,
        "offset": offset,
        "limit": limit,
    }
    if sort_by:
        params["sort_by"] = sort_by

    response = requests.get(YELP_SEARCH_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_live_businesses(term, location, pages=1, sort_by=None):
    rows = []

    for page in range(pages):
        offset = page * PAGE_SIZE
        payload = fetch_yelp_page(term, location, offset=offset, sort_by=sort_by)
        businesses = payload.get("businesses", [])

        if not businesses:
            break

        rows.extend(business_to_row(business) for business in businesses)

    return clean_dataframe(pd.DataFrame(rows, columns=OUTPUT_COLUMNS))


def load_offline_results(location, term, limit=PAGE_SIZE):
    path = CITY_DATASETS.get(location)
    if not path:
        path = DATA_DIR / "mergedtable.csv"

    df = clean_dataframe(pd.read_csv(path))
    term = (term or "").strip().lower()
    if term and term not in ("restaurant", "restaurants", "food"):
        mask = (
            df["Category"].fillna("").str.lower().str.contains(term, regex=False)
            | df["Business"].fillna("").str.lower().str.contains(term, regex=False)
        )
        filtered = df[mask]
        if not filtered.empty:
            df = filtered

    return df.sort_values(["Reviews", "Rating"], ascending=[False, False]).head(limit)


def summarize(df):
    if df.empty:
        return {
            "result_count": 0,
            "average_rating": 0,
            "average_reviews": 0,
            "top_category": "None",
            "category_breakdown": [],
            "rating_breakdown": [],
        }

    category_counts = df["Category"].fillna("Uncategorized").value_counts().head(8)
    rating_groups = (
        df.groupby("Rating", dropna=False)["Business"]
        .count()
        .reset_index(name="Count")
        .sort_values("Rating", ascending=False)
    )

    return {
        "result_count": int(len(df)),
        "average_rating": round(float(df["Rating"].mean()), 2),
        "average_reviews": int(round(float(df["Reviews"].mean()))),
        "top_category": str(category_counts.index[0]),
        "category_breakdown": [
            {"label": str(label), "count": int(count)}
            for label, count in category_counts.items()
        ],
        "rating_breakdown": [
            {"label": f"{row.Rating:.1f}", "count": int(row.Count)}
            for row in rating_groups.itertuples(index=False)
        ],
    }


def rows_for_response(df, limit=20):
    records = []
    for row in df.head(limit).itertuples(index=False):
        records.append(
            {
                "business": row.Business,
                "city": row.City,
                "state": row.State,
                "category": row.Category,
                "price": int(row.Price or 0),
                "reviews": int(row.Reviews or 0),
                "rating": round(float(row.Rating or 0), 1),
            }
        )
    return records
