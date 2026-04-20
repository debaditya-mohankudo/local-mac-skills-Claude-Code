"""
market_pulse.py
Fetches historical market data from the start of the June 2025
Twelve-Day War through today — giving the full context window
for the Iran-Gulf War 2026 portfolio analysis.

Tickers are defined in portfolio_state.yaml [tickers] — add/remove there.
- Fixed start date: 2026-01-01 (historical pre-2026 already in SQLite)
- Retries up to MAX_RETRIES times per ticker
- Writes directly to market_intel.sqlite (no parquet intermediary)
- Uses polars for fast, clean dataframe handling
"""

import os
import sqlite3
import time
import pytz
import yfinance as yf
import polars as pl
from datetime import datetime, date
from config import TICKERS

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds between retries

START_DATE = date(2026, 1, 1)

DB_PATH = os.path.expanduser("~/Documents/claude_cache_data/market-intel/market_intel.sqlite")

# Mapping: polars column name (from yfinance label) → SQLite column name
_COL_MAP = {
    "DXY":      "dxy",
    "Brent":    "brent",
    "Gold":     "gold",
    "Nifty50":  "nifty50",
    "USDINR":   "usdinr",
    "IndiaVIX": "india_vix",
    "USDJPY":   "usdjpy",
    "Nasdaq":   "nasdaq",
    "US10Y":    "us10y",
}
# Reverse map: sqlite col → polars label
_COL_MAP_REV = {v: k for k, v in _COL_MAP.items()}


def fetch_history(label: str, symbol: str, start: date = START_DATE) -> pl.DataFrame | None:
    """Fetch daily close history for a symbol with retry logic. Returns a polars DataFrame."""
    end = datetime.today()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  [{attempt}/{MAX_RETRIES}] Fetching {label} ({symbol}) ...")
            raw = yf.download(
                symbol,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True,
            )
            if raw is not None and not raw.empty:
                if hasattr(raw.columns, "levels"):
                    raw.columns = [col[0] for col in raw.columns]
                df = pl.from_pandas(raw[["Close"]].reset_index())
                df = df.rename({"Close": label, "Date": "Date"})
                df = df.with_columns(pl.col("Date").cast(pl.Date))
                print(f"         ✓ {len(df)} rows retrieved")
                return df
            else:
                print(f"         ✗ Empty response (attempt {attempt})")

        except Exception as e:
            print(f"         ✗ Error: {e} (attempt {attempt})")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    print(f"  ✗ Failed to fetch {label} after {MAX_RETRIES} attempts — skipping.\n")
    return None


def _upsert_to_sqlite(df: pl.DataFrame, db_path: str = DB_PATH) -> int:
    """Upsert a polars DataFrame (with Date + ticker columns) into market_prices SQLite table.

    Uses INSERT OR REPLACE so existing rows are updated and new rows are added.
    Returns number of rows upserted.
    """
    db_path = os.path.expanduser(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Rename polars labels → SQLite column names
    rename = {k: v for k, v in _COL_MAP.items() if k in df.columns}
    df_db = df.rename(rename)
    if "Date" in df_db.columns:
        df_db = df_db.rename({"Date": "date"})

    # Ensure all expected columns exist (fill missing with null)
    all_cols = ["date"] + list(_COL_MAP.values())
    for col in all_cols:
        if col not in df_db.columns:
            df_db = df_db.with_columns(pl.lit(None).cast(pl.Float64).alias(col))
    df_db = df_db.select(all_cols)

    # Convert date to string for SQLite
    df_db = df_db.with_columns(pl.col("date").cast(pl.Utf8))

    rows = df_db.to_dicts()
    cols = all_cols
    placeholders = ", ".join(["?"] * len(cols))
    col_names = ", ".join(cols)

    with sqlite3.connect(db_path) as con:
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS market_prices (
                date TEXT PRIMARY KEY,
                dxy REAL, brent REAL, gold REAL, nifty50 REAL,
                usdinr REAL, india_vix REAL, usdjpy REAL, nasdaq REAL, us10y REAL
            )
        """)
        con.executemany(
            f"INSERT OR REPLACE INTO market_prices ({col_names}) VALUES ({placeholders})",
            [[row.get(c) for c in cols] for row in rows],
        )
        con.commit()

    return len(rows)


def get_data_from_db(db_path: str = DB_PATH) -> pl.DataFrame | None:
    """Read all market_prices from SQLite and return a polars DataFrame.

    Column names are mapped back to the canonical polars labels (Nifty50, Gold, etc.)
    so all callers that previously used get_data_from_cache() work unchanged.
    """
    db_path = os.path.expanduser(db_path)
    if not os.path.exists(db_path):
        print(f"  ✗ SQLite DB not found: {db_path} — run get_history_all() to populate.")
        return None

    with sqlite3.connect(db_path) as con:
        cur = con.execute("SELECT * FROM market_prices ORDER BY date")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

    if not rows:
        print("  ✗ market_prices table is empty.")
        return None

    df = pl.DataFrame(rows, schema=cols, orient="row")
    # Rename date → Date, sqlite cols → polars labels
    rename = {"date": "Date"}
    rename.update(_COL_MAP_REV)
    df = df.rename({k: v for k, v in rename.items() if k in df.columns})
    df = df.with_columns(pl.col("Date").cast(pl.Date))

    print(f"  ✅ Loaded market_prices from SQLite → {len(df)} rows")
    print(f"     Date range: {df['Date'].min()} → {df['Date'].max()}")

    return df


def save_market_data(df: pl.DataFrame) -> int:
    """Public API: persist a market DataFrame to the backing store.

    Callers should use this instead of _upsert_to_sqlite directly.
    Swap the implementation (SQLite → DuckDB, cloud, etc.) here without
    touching any caller.
    """
    return _upsert_to_sqlite(df)


def load_market_data() -> pl.DataFrame | None:
    """Public API: load all market prices from the backing store.

    Returns a polars DataFrame with canonical column names (Date, Nifty50, Gold, …).
    Callers should use this instead of get_data_from_db directly.
    """
    return get_data_from_db()


# Legacy aliases — keep so existing callers don't break
get_data_from_cache = load_market_data


def get_history_all() -> pl.DataFrame:
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist).strftime("%Y-%m-%d %H:%M IST")

    print(f"\n{'='*58}")
    print(f"  📊 Market Pulse — {START_DATE} → today — {now}")
    print(f"{'='*58}\n")

    frames = []
    for label, symbol in TICKERS.items():
        df = fetch_history(label, symbol)
        if df is not None:
            frames.append(df)

    if not frames:
        print("  ✗ No data retrieved. Check your network or ticker symbols.\n")
        return pl.DataFrame()

    # Join all tickers on Date
    combined = frames[0]
    for df in frames[1:]:
        combined = combined.join(df, on="Date", how="full", coalesce=True)

    combined = combined.sort("Date")

    # Drop rows where ALL market columns are null
    market_cols = [c for c in combined.columns if c != "Date"]
    if market_cols:
        combined = combined.filter(
            ~pl.all_horizontal([pl.col(c).is_null() for c in market_cols])
        )

    print(f"\n{'='*58}")
    print(f"  Summary — Last 5 rows")
    print(f"{'='*58}")
    print(combined.tail(5))

    n = save_market_data(combined)
    print(f"\n  ✅ Saved {n} rows → backing store")
    print(f"  Total fetched: {len(combined)} rows\n")

    return combined


if __name__ == "__main__":
    get_history_all()
