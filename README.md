# Yelp Analytics Project

![Yelp](data/yelppng.png)

## Project Scope

This project uses Yelp restaurant data to compare markets in four regions of the
United States:

* New York, NY - East
* Austin, TX - South
* Chicago, IL - North
* San Francisco, CA - West

The analysis looks at restaurant categories, review volume, ratings, and market
density. A separate burger-focused analysis for New Brunswick, NJ is also
included.

## Project Contents

* `data/` - committed CSV exports used by the existing analyses
* `plots/` - generated charts from the historical analysis
* `ProjectMaster-Final Copy.ipynb` - main historical analysis notebook
* `Battle of Burgers from Most Popular Cities.ipynb` - burger comparison notebook
* `Highest Reviewed Restaurant in New Brunswick.ipynb` - New Brunswick notebook
* `YelpSearchProgram.py` - standalone Yelp API export script
* `app.py` - Flask web app for exploring Yelp-style market results
* `Final_Presentation.pptx` - final project presentation
* `oldrevs/` - older notebook revisions

## Local Setup

The committed CSV files in `data/` are enough to review and rerun much of the
historical analysis without calling an external API. To refresh data from Yelp
or render Google Maps notebook output, you need local API keys.

Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a local `config.py` file from the template:

```bash
copy config.example.py config.py
```

Then edit `config.py` and add your keys:

```python
api_key = "your-yelp-api-key"
gkey = "your-google-maps-api-key"
```

`config.py` is ignored by git and should not be committed.

Alternatively, set `YELP_API_KEY` in your shell for a one-off run without
creating `config.py`.

## Standalone Yelp Search

`YelpSearchProgram.py` accesses Yelp's Business Search API and exports results
to CSV for further analysis.

Interactive mode:

```bash
python YelpSearchProgram.py
```

Command-line mode:

```bash
python YelpSearchProgram.py --term Restaurants --location "New York City, NY" --pages 4 --output data/NewYork_refresh.csv
```

Each page fetches up to 50 Yelp results. For example, `--pages 4` requests
offsets `0`, `50`, `100`, and `150`.

## Web App

This repo includes a small Flask web app that turns the CSV analysis into a
usable browser experience.

Run it locally:

```bash
python app.py
```

The app works in two modes:

* `Demo CSV` reads the committed CSV files in `data/`
* `Live Yelp API` uses the server-side `YELP_API_KEY` environment variable

The key is never exposed to browser JavaScript.

## Render Deployment

The app is Render-ready through `render.yaml` and `Procfile`.

On Render:

1. Create a new web service from this repository.
2. Use `pip install -r requirements.txt` as the build command.
3. Use `gunicorn app:app` as the start command.
4. Add `YELP_API_KEY` as an environment variable if live search should be
   enabled.

## Inputs Needed to Fully Reconnect

To fully reconnect and refresh this project, supply these local-only values:

* Yelp Fusion API key for `api_key`
* Google Maps API key for `gkey`

The next rework step is to consolidate the final notebook workflow and move
older notebook revisions into a clearer archive structure.
