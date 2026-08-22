import os
from pathlib import Path

import pandas as pd
import requests
from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PAGE_SIZE = 50
YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

CITY_DATASETS = {
    "Austin, TX": DATA_DIR / "AustinTX.csv",
    "Chicago, IL": DATA_DIR / "Chicago.csv",
    "New York, NY": DATA_DIR / "NewYork.csv",
    "San Francisco, CA": DATA_DIR / "SanFrancisco.csv",
    "New Brunswick, NJ": DATA_DIR / "New Brunswick, NJ_Burger.csv",
}

REQUIRED_COLUMNS = [
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

app = Flask(__name__)


def normalize_price(price):
    if pd.isna(price) or price in ("", "0", 0):
        return 0
    if isinstance(price, str) and price.startswith("$"):
        return len(price)
    try:
        return int(price)
    except (TypeError, ValueError):
        return 0


def clean_dataframe(df):
    df = df.copy()
    unnamed_columns = [col for col in df.columns if col.startswith("Unnamed")]
    if unnamed_columns:
        df = df.drop(columns=unnamed_columns)

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[REQUIRED_COLUMNS]
    df["Price"] = df["Price"].apply(normalize_price)
    df["Reviews"] = pd.to_numeric(df["Reviews"], errors="coerce").fillna(0).astype(int)
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0.0)
    return df.drop_duplicates(subset=["Business ID"])


def load_offline_results(location, term):
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

    return df.sort_values(["Reviews", "Rating"], ascending=[False, False]).head(PAGE_SIZE)


def fetch_live_results(location, term):
    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        return None

    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "term": term or "Restaurants",
        "location": location,
        "limit": PAGE_SIZE,
        "sort_by": "review_count",
    }
    response = requests.get(YELP_SEARCH_URL, headers=headers, params=params, timeout=20)
    response.raise_for_status()

    rows = []
    for business in response.json().get("businesses", []):
        categories = business.get("categories") or [{}]
        coordinates = business.get("coordinates") or {}
        business_location = business.get("location") or {}
        rows.append(
            {
                "Business": business.get("name"),
                "Business ID": business.get("id"),
                "City": business_location.get("city"),
                "State": business_location.get("state"),
                "Category": categories[0].get("title"),
                "Latitude": coordinates.get("latitude"),
                "Longitude": coordinates.get("longitude"),
                "Price": normalize_price(business.get("price")),
                "Reviews": business.get("review_count"),
                "Rating": business.get("rating"),
            }
        )

    return clean_dataframe(pd.DataFrame(rows, columns=REQUIRED_COLUMNS))


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


def rows_for_response(df):
    records = []
    for row in df.head(20).itertuples(index=False):
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


@app.route("/")
def index():
    return render_template(
        "index.html",
        cities=list(CITY_DATASETS.keys()),
        live_enabled=bool(os.getenv("YELP_API_KEY")),
    )


@app.route("/api/search")
def search():
    location = request.args.get("location", "New York, NY")
    term = request.args.get("term", "Restaurants")
    mode = request.args.get("mode", "demo")

    source = "Demo CSV"
    try:
        if mode == "live":
            live_df = fetch_live_results(location, term)
            if live_df is not None:
                df = live_df
                source = "Live Yelp API"
            else:
                df = load_offline_results(location, term)
                source = "Demo CSV - set YELP_API_KEY for live search"
        else:
            df = load_offline_results(location, term)
    except requests.RequestException as exc:
        df = load_offline_results(location, term)
        source = f"Demo CSV - live search failed: {exc.response.status_code if exc.response else 'request error'}"

    return jsonify(
        {
            "source": source,
            "location": location,
            "term": term,
            "summary": summarize(df),
            "businesses": rows_for_response(df),
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
