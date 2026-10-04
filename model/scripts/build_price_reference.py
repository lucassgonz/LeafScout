#!/usr/bin/env python3
"""Build a small, static market-price reference snapshot for each crop, from
real WFP food price data (via HDX) — this is the direct fix for the problem
named in the hackathon's own Annex B scenario: "at harvest she sells her
parchment to whichever middleman drives up the valley, at whatever price he
names." An independent reference price is the thing that changes that.

Not a live feed: WFP updates monthly and this is a point-in-time snapshot,
refreshed by re-running this script. Coffee isn't in WFP's food-security
price basket (it's a cash crop, not a food staple) in most countries, so we
use Ethiopia's dataset, the one major coffee-producing country where WFP
does track it; bean and cassava prices come from Uganda, matching the
iBean/cassava datasets' origin.

Run:
    ./.venv/bin/python scripts/build_price_reference.py
Requires raw/prices/wfp_ethiopia.csv and raw/prices/wfp_uganda.csv —
download from data.humdata.org/dataset/wfp-food-prices-for-ethiopia and
.../wfp-food-prices-for-uganda first (the "Food Prices" CSV resource).
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICES_DIR = ROOT / "raw" / "prices"
OUT_PATHS = [
    ROOT.parent / "web" / "assets" / "data" / "market_prices.json",
    # Named marketPricesData.json, not marketPrices.json — Metro's resolver
    # treats an extension-less `from '../data/marketPrices'` import as
    # ambiguous between a .json and a .ts file of the same base name, and
    # picked the raw JSON over app/src/data/marketPrices.ts's actual
    # exports (marketPriceFor, etc.), crashing at runtime with "undefined
    # is not a function". Caught live on iOS Simulator.
    ROOT.parent / "app" / "src" / "data" / "marketPricesData.json",
]

# (crop_id, csv_file, commodity_name, reference_country, unit_label)
SOURCES = [
    ("coffee", "wfp_ethiopia.csv", "Coffee", "Ethiopia", "kg"),
    ("bean", "wfp_uganda.csv", "Beans", "Uganda", "kg"),
    ("cassava", "wfp_uganda.csv", "Cassava (fresh)", "Uganda", "kg"),
]
TREND_MONTHS = 6


def monthly_series(path: Path, commodity: str) -> list[dict]:
    by_date: dict[str, list[float]] = defaultdict(list)
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["commodity"] == commodity and row.get("pricetype") == "Retail" and row["usdprice"]:
                by_date[row["date"]].append(float(row["usdprice"]))

    dates = sorted(by_date.keys())
    return [
        {"date": d, "avg_usd_per_kg": round(sum(by_date[d]) / len(by_date[d]), 3), "n_markets": len(by_date[d])}
        for d in dates
    ]


def main() -> None:
    result = {}
    for crop_id, csv_name, commodity, country, unit in SOURCES:
        series = monthly_series(PRICES_DIR / csv_name, commodity)
        if not series:
            raise SystemExit(f"No data found for {commodity} in {csv_name} — check the commodity name/column.")
        trend = series[-TREND_MONTHS:]
        latest = trend[-1]
        result[crop_id] = {
            "commodity": commodity,
            "reference_country": country,
            "unit": unit,
            "latest_date": latest["date"],
            "latest_avg_usd_per_kg": latest["avg_usd_per_kg"],
            "latest_n_markets": latest["n_markets"],
            "trend": trend,
            "source": "WFP Food Prices via HDX (data.humdata.org)",
            "note": (
                "Monthly snapshot, not a live feed. Coffee is tracked via Ethiopia "
                "(not usually in WFP's food-security basket elsewhere); bean and "
                "cassava via Uganda, matching this project's training data origin."
            ),
        }

    for out_path in OUT_PATHS:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2))
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
