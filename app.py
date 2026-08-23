import os

import requests
from flask import Flask, jsonify, render_template, request

from yelp_service import (
    CITY_DATASETS,
    get_api_key,
    load_offline_results,
    rows_for_response,
    search_live_businesses,
    summarize,
)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html",
        cities=list(CITY_DATASETS.keys()),
        live_enabled=bool(get_api_key(required=False)),
    )


@app.route("/api/search")
def search():
    location = request.args.get("location", "New York, NY")
    term = request.args.get("term", "Restaurants")
    mode = request.args.get("mode", "demo")

    source = "Demo CSV"
    try:
        if mode == "live" and get_api_key(required=False):
            df = search_live_businesses(term, location, pages=1, sort_by="review_count")
            source = "Live Yelp API"
        elif mode == "live":
            df = load_offline_results(location, term)
            source = "Demo CSV - set YELP_API_KEY for live search"
        else:
            df = load_offline_results(location, term)
    except requests.RequestException as exc:
        df = load_offline_results(location, term)
        status = exc.response.status_code if exc.response else "request error"
        source = f"Demo CSV - live search failed: {status}"

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
