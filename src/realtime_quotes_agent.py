#!/usr/bin/env python3
"""Realtime quote fetcher — yfinance primary, Google Finance fallback via osascript/JS."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import json
import re
import subprocess

import yfinance as yf


_YAHOO_TO_GOOGLE = {
    "BZ=F": "ICEEUR:BRN",
    "GC=F": "COMEX:GC1!",
    "DX-Y.NYB": "INDEXNYSEGIS:DXY",
    "^NSEI": "INDEXNSE:NIFTY_50",
    "INR=X": "CURRENCYCOM:USDINR",
    "^INDIAVIX": "INDEXNSE:INDIA_VIX",
    "JPY=X": "CURRENCYCOM:USDJPY",
    "^IXIC": "INDEXNASDAQ:.IXIC",
    "^TNX": "INDEXCBOE:TNX",
    "CL=F": "NYMEX:CL1!",
}


def _to_google_symbol(symbol: str) -> str:
    s = symbol.strip()
    if ":" in s:
        return s
    return _YAHOO_TO_GOOGLE.get(s, s)


def _parse_price(raw: str) -> float:
    cleaned = re.sub(r"[^0-9.\-]", "", raw.replace(",", ""))
    if cleaned in {"", "-", ".", "-."}:
        raise ValueError(f"could not parse numeric price from {raw!r}")
    return round(float(cleaned), 2)


def _fetch_yfinance(symbol: str) -> float:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d", interval="1m", prepost=True)
    if hist is None or hist.empty:
        hist = ticker.history(period="5d", interval="1d")
    if hist is None or hist.empty:
        raise ValueError(f"no yfinance history for {symbol}")
    close = hist["Close"].dropna()
    if close.empty:
        raise ValueError(f"no close values for {symbol}")
    return round(float(close.iloc[-1]), 2)


def _fetch_google_via_osascript(google_symbol: str) -> float:
    """
    Fetch Google Finance price via Safari JavaScript (prices are JS-rendered,
    not accessible via requests/BeautifulSoup).
    """
    url = f"https://www.google.com/finance/quote/{google_symbol}?hl=en"
    script = f"""
    tell application "Safari"
        set theURL to "{url}"
        set theTab to make new document with properties {{URL:theURL}}
        delay 3
        set thePrice to do JavaScript "
            var el = document.querySelector('.YMlKec.fxKbKc');
            el ? el.innerText : '';
        " in front document
        close front document
        return thePrice
    end tell
    """
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", script],
        capture_output=True, text=True, timeout=20
    )
    raw = result.stdout.strip()
    if not raw:
        raise ValueError("Google Finance JS returned empty price")
    return _parse_price(raw)


def _fetch_one(name: str, symbol: str) -> tuple[str, float | None, str | None]:
    """Fetch a single ticker: yfinance primary, Google Finance fallback."""
    try:
        return name, _fetch_yfinance(symbol), None
    except Exception as yf_err:
        google_symbol = _to_google_symbol(symbol)
        try:
            return name, _fetch_google_via_osascript(google_symbol), None
        except Exception as gf_err:
            return name, None, f"yfinance: {yf_err}; google: {gf_err}"


def fetch_realtime_quotes(
    tickers: dict[str, str],
    cache_dir: str | Path | None = None,
    overwrite_today: bool = False,
) -> dict:
    """
    Fetch live quotes for the provided ticker map in parallel.
    yfinance is primary; Google Finance (via Safari JS) is the fallback.

    Args:
        tickers: Mapping like {"Brent": "BZ=F", "Nifty50": "^NSEI"}
        cache_dir: Optional directory for intraday JSON snapshots.
        overwrite_today: If True, keep only one snapshot (latest).
    """
    quotes: dict[str, float] = {}
    errors: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=len(tickers)) as pool:
        futures = {pool.submit(_fetch_one, name, sym): name for name, sym in tickers.items()}
        for fut in as_completed(futures, timeout=60):
            name, price, error = fut.result()
            if price is not None:
                quotes[name] = price
            else:
                errors[name] = error or "unknown"

    now = datetime.now()
    result = {
        "quotes": quotes,
        "errors": errors,
        "source": "yfinance (Google Finance fallback)",
        "timestamp": now.isoformat(),
    }

    if not quotes or cache_dir is None:
        return result

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    intraday_file = cache_path / f"intraday_{now.strftime('%Y-%m-%d')}.json"

    if overwrite_today:
        snapshots = [{"time": now.strftime("%H:%M:%S"), **quotes}]
    else:
        if intraday_file.exists():
            snapshots = json.loads(intraday_file.read_text())
        else:
            snapshots = []
        snapshots.append({"time": now.strftime("%H:%M:%S"), **quotes})

    intraday_file.write_text(json.dumps(snapshots, indent=2))


    result["intraday_file"] = str(intraday_file)
    result["snapshots_today"] = len(snapshots)
    return result


if __name__ == "__main__":
    from config import VAULT_DAILY_DIR
    from config import TICKERS

    cache_dir = VAULT_DAILY_DIR
    output = fetch_realtime_quotes(tickers=TICKERS, cache_dir=cache_dir, overwrite_today=False)
    print(json.dumps(output, indent=2))
