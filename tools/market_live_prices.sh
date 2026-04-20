#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv run python - <<'PY'
from datetime import datetime
import sys
import yfinance as yf

sys.path.insert(0, "src")

from config import TICKERS
from realtime_quotes_agent import fetch_realtime_quotes


def fmt_pct(v):
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"


def get_day_change_pct(symbol: str):
    try:
        hist = yf.Ticker(symbol).history(period="2d", interval="1d")
        close = hist["Close"].dropna()
        if len(close) >= 2 and close.iloc[-2] != 0:
            return ((float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2])) * 100.0
    except Exception:
        return None
    return None


asset_to_key = {
    "Brent": "Brent",
    "Gold": "Gold",
    "DXY": "DXY",
    "Nifty 50": "Nifty50",
    "USD/INR": "USDINR",
    "India VIX": "IndiaVIX",
    "USD/JPY": "USDJPY",
    "Nasdaq": "Nasdaq",
    "US 10Y": "US10Y",
}

result = fetch_realtime_quotes(TICKERS, cache_dir=None, overwrite_today=False)
quotes = result.get("quotes", {})

changes = {}
for key, symbol in TICKERS.items():
    changes[key] = get_day_change_pct(symbol)

print(f"## Live Prices — {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
print()
print("| Asset | Price | Change |")
print("|---|---:|:---:|")

for asset, key in asset_to_key.items():
    price = quotes.get(key)
    change = changes.get(key)
    if price is None:
        price_str = "N/A"
    else:
        price_str = f"{price:.2f}"
    if asset == "USD/INR":
        price_str = f"₹{price_str}" if price_str != "N/A" else "₹N/A"
    print(f"| {asset} | {price_str} | {fmt_pct(change)} |")

brent_pct = changes.get("Brent")
gold_pct = changes.get("Gold")
nifty_pct = changes.get("Nifty50")
india_vix = quotes.get("IndiaVIX")

oil_drop_fired = brent_pct is not None and brent_pct < -15
gold_drop_fired = gold_pct is not None and gold_pct < -4
vix_fired = india_vix is not None and india_vix < 20
nifty_fired = nifty_pct is not None and nifty_pct > 5

count = int(oil_drop_fired) + int(gold_drop_fired) + int(vix_fired) + int(nifty_fired)
status = "WATCH"
if count == 4:
    status = "CONFIRMED"
elif count > 0:
    status = "ACTIVE"

print()
print("| Signal | Threshold | Fired? |")
print("|--|--:|:--:|")
print(f"| Oil drop | > −15% | {'✅' if oil_drop_fired else '❌'} |")
print(f"| Gold drop | > −4% | {'✅' if gold_drop_fired else '❌'} |")
print(f"| VIX below 20 | < 20 | {'✅' if vix_fired else '❌'} |")
print(f"| Nifty gain | > +5% | {'✅' if nifty_fired else '❌'} |")
print()
print(f"{count}/4 signals fired")
print(f"Status: {status}")
PY
