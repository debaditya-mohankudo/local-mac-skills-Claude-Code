#!/usr/bin/env python3
"""Fetch live prices for all monitored tickers via yfinance (local uv env).

Usage:
  uv run python tools/yahoo_prices.py
Returns JSON to stdout.
"""

import json
import sys

import yfinance as yf

TICKERS = {
    "Brent":    "BZ=F",
    "Gold":     "GC=F",
    "DXY":      "DX-Y.NYB",
    "Nifty50":  "^NSEI",
    "USDINR":   "INR=X",
    "IndiaVIX": "^INDIAVIX",
    "USDJPY":   "JPY=X",
    "Nasdaq":   "^IXIC",
    "US10Y":    "^TNX",
}


def main():
    quotes = {}
    errors = {}

    data = yf.download(
        list(TICKERS.values()),
        period="5d",
        interval="1m",
        progress=False,
        auto_adjust=True,
    )

    close = data["Close"] if "Close" in data.columns else data.xs("Close", axis=1, level=0)

    for name, symbol in TICKERS.items():
        try:
            series = close[symbol].dropna()
            if series.empty:
                errors[name] = "no data"
            else:
                quotes[name] = round(float(series.iloc[-1]), 4)
        except Exception as e:
            errors[name] = str(e)

    print(json.dumps({
        "quotes": quotes,
        "errors": errors,
        "source": "Yahoo Finance via yfinance/uv",
    }, indent=2))


if __name__ == "__main__":
    main()
