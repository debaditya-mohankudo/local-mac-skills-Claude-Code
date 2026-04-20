"""
tools.py — Market intelligence tool functions called from Swift MCP layer.

Exports:
  get_gold_regime_history()      → regime history with current, streak, momentum, gate0/trim counts
  get_gold_regime_projection()   → next-regime probabilities with geo-context adjustment
  (other market tools as they're needed)

All functions return JSON-serializable dicts (no numpy/polars objects).
"""

from datetime import datetime, timedelta
from collections import Counter
import polars as pl

from market_pulse import get_data_from_cache
from portfolio_state import (
    GEO, GOLD_TRIM, ALLOCATION, RISK_CONTROLS, DEPLOYMENT_PLAN, CEASEFIRE,
    DEPLOYMENT_LOG
)


# ── Regime Classification ──────────────────────────────────────────────────────

def _classify_regime(gold_chg: float, nifty_chg: float, dxy_chg: float) -> tuple[str, str]:
    """
    Classify a single day into one of 5 regimes based on daily % changes.

    Returns: (regime_name, flag)
    Flags: "X" = Gate 0 veto, "T" = Trim candidate, "" = neutral

    Regime logic (checked in order):
    1. Liquidity Crunch: gold < 0 AND nifty < 0 AND dxy > 0
    2. War Premium Unwind: gold < 0 AND nifty > 0 AND abs(dxy) <= 0.3
    3. Macro Headwind: gold < 0 AND dxy > 0 (stocks mixed)
    4. Equity Rotation: gold <= 0.1 AND nifty > 0 AND abs(dxy) <= 0.3
    5. Secular Continuation: gold > 0 (fallback)
    """
    # Handle None/NaN values
    if gold_chg is None or nifty_chg is None or dxy_chg is None:
        return "Unknown", ""

    flag = ""

    # Gate 0 veto triggers
    if gold_chg < -1.5 or nifty_chg < -2.0:
        flag = "X"

    # Classify regime
    if gold_chg < 0 and nifty_chg < 0 and dxy_chg > 0:
        return "Liquidity Crunch", flag

    if gold_chg < 0 and nifty_chg > 0 and abs(dxy_chg) <= 0.3:
        regime = "War Premium Unwind"
        if flag != "X":  # Only trim if no Gate 0 veto
            flag = "T"
        return regime, flag

    if gold_chg < 0 and dxy_chg > 0:
        return "Macro Headwind", flag

    if gold_chg <= 0.1 and nifty_chg > 0 and abs(dxy_chg) <= 0.3:
        regime = "Equity Rotation"
        if flag != "X":
            flag = "T"
        return regime, flag

    # Fallback: Secular Continuation (gold > 0 or any other pattern)
    return "Secular Continuation", flag


def get_gold_regime_history() -> dict:
    """
    Load gold/nifty/DXY history from cache, compute daily % changes,
    classify into 5 regimes, return current regime + 5-day momentum + stats.
    """
    df = get_data_from_cache()
    if df is None or len(df) == 0:
        return {
            "current_regime": "Unknown",
            "streak_days": 0,
            "momentum_5d": {"gold": 0.0, "nifty": 0.0, "dxy": 0.0},
            "recent_5": [],
            "regime_counts": {},
            "gate0_veto_days": 0,
            "trim_candidate_days": 0,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }

    # Ensure Date column is parsed as date
    if df["Date"].dtype != pl.Date:
        df = df.with_columns(pl.col("Date").str.to_date())

    # Sort by date ascending
    df = df.sort("Date")

    # Compute daily % changes
    df = df.with_columns([
        ((pl.col("Gold").pct_change() * 100).round(3)).alias("gold_pct"),
        ((pl.col("Nifty50").pct_change() * 100).round(3)).alias("nifty_pct"),
        ((pl.col("DXY").pct_change() * 100).round(3)).alias("dxy_pct"),
    ])

    # Skip rows with any NaN % changes
    df = df.filter(
        pl.col("gold_pct").is_not_null() &
        pl.col("nifty_pct").is_not_null() &
        pl.col("dxy_pct").is_not_null()
    )

    # Classify each row into regime + flag
    regimes = []
    flags = []
    for row in df.iter_rows(named=True):
        regime, flag = _classify_regime(
            row["gold_pct"],
            row["nifty_pct"],
            row["dxy_pct"]
        )
        regimes.append(regime)
        flags.append(flag)

    df = df.with_columns([
        pl.Series("regime", regimes),
        pl.Series("flag", flags),
    ])

    # Current regime (last row)
    current_regime = df["regime"][-1]

    # Streak: count consecutive current regime days from end
    streak = 1
    regime_col = df["regime"].to_list()
    for i in range(len(regime_col) - 2, -1, -1):
        if regime_col[i] == current_regime:
            streak += 1
        else:
            break

    # 5-day momentum (average daily % change for last 5 rows)
    last_5 = df[-5:]
    gold_mom = (last_5["gold_pct"].mean() or 0.0)
    nifty_mom = (last_5["nifty_pct"].mean() or 0.0)
    dxy_mom = (last_5["dxy_pct"].mean() or 0.0)

    # Recent 5 days (newest first)
    recent_5_rows = []
    last_5 = df.tail(5)
    for row in last_5.iter_rows(named=True):
        recent_5_rows.insert(0, {
            "date": row["Date"].isoformat() if hasattr(row["Date"], "isoformat") else str(row["Date"]),
            "gold_pct": round(row["gold_pct"], 2),
            "nifty_pct": round(row["nifty_pct"], 2),
            "dxy_pct": round(row["dxy_pct"], 2),
            "regime": row["regime"],
            "flag": row["flag"],
        })

    # Regime counts (all-time)
    regime_counts = dict(Counter(df["regime"]))

    # Gate 0 veto + trim candidate days
    gate0_days = (df["flag"] == "X").sum()
    trim_days = (df["flag"] == "T").sum()

    # Last updated date
    last_date = df["Date"][-1]
    last_updated = last_date.isoformat() if hasattr(last_date, "isoformat") else str(last_date)

    return {
        "current_regime": current_regime,
        "streak_days": int(streak),
        "momentum_5d": {
            "gold": round(gold_mom, 3),
            "nifty": round(nifty_mom, 3),
            "dxy": round(dxy_mom, 3),
        },
        "recent_5": recent_5_rows,
        "regime_counts": regime_counts,
        "gate0_veto_days": int(gate0_days),
        "trim_candidate_days": int(trim_days),
        "last_updated": last_updated,
    }


# ── Market Data & Signals (legacy Python APIs) ────────────────────────────────────

def get_latest_market_data() -> dict:
    """Load latest market prices from SQLite. Returns dict of tickers + EOD timestamp."""
    df = get_data_from_cache()
    if df is None or len(df) == 0:
        return {"error": "No market data found", "status": "cache_empty"}

    latest = df.tail(1).to_dicts()[0]
    return {
        "date": str(latest.get("Date", "")),
        "Brent": latest.get("Brent"),
        "Gold": latest.get("Gold"),
        "Nifty50": latest.get("Nifty50"),
        "DXY": latest.get("DXY"),
        "USDINR": latest.get("USDINR"),
        "IndiaVIX": latest.get("IndiaVIX"),
        "USDJPY": latest.get("USDJPY", 0),
        "Nasdaq": latest.get("Nasdaq", 0),
        "US10Y": latest.get("US10Y", 0),
    }


def check_ceasefire_signals() -> dict:
    """Check how many of 4 ceasefire signals have fired. Returns signal status + action."""
    from portfolio_state import CEASEFIRE

    df = get_data_from_cache()
    if df is None or len(df) < 2:
        return {"error": "Insufficient data for signal check"}

    df = df.sort("Date")
    today = df.tail(1).to_dicts()[0]
    prev = df.tail(2)[0].to_dicts()[0]

    # Compute daily % changes
    def pct(curr_val, prev_val):
        if prev_val is None or prev_val == 0 or curr_val is None:
            return 0
        return ((curr_val - prev_val) / prev_val) * 100

    brent_chg = pct(today.get("Brent"), prev.get("Brent"))
    gold_chg = pct(today.get("Gold"), prev.get("Gold"))
    nifty_chg = pct(today.get("Nifty50"), prev.get("Nifty50"))
    current_vix = today.get("IndiaVIX") or 25

    # Signal fire checks
    oil_fired = brent_chg <= CEASEFIRE.oil_drop_pct
    gold_fired = gold_chg >= CEASEFIRE.gold_rise_pct
    vix_fired = current_vix <= CEASEFIRE.vix_below
    nifty_fired = nifty_chg >= CEASEFIRE.nifty_gain_pct

    signals_fired = sum([oil_fired, gold_fired, vix_fired, nifty_fired])

    if signals_fired >= CEASEFIRE.min_signals_required + 1:
        status = "confirmed"
        action = "rotate_gold_to_dsp"
    elif signals_fired >= CEASEFIRE.min_signals_required:
        status = "watch"
        action = "verify"
    else:
        status = "active"
        action = "hold"

    return {
        "date": str(today.get("Date", "")),
        "signals_fired": signals_fired,
        "status": status,
        "signals": {
            "oil_drop": {"fired": oil_fired, "value": round(brent_chg, 2), "threshold": CEASEFIRE.oil_drop_pct},
            "gold_rise": {"fired": gold_fired, "value": round(gold_chg, 2), "threshold": CEASEFIRE.gold_rise_pct},
            "vix_below": {"fired": vix_fired, "value": round(current_vix, 2), "threshold": CEASEFIRE.vix_below},
            "nifty_gain": {"fired": nifty_fired, "value": round(nifty_chg, 2), "threshold": CEASEFIRE.nifty_gain_pct},
        },
        "action": action,
    }


def check_deployment_triggers() -> dict:
    """Check Nifty drawdown vs tranche trigger levels. Returns deployment eligibility."""
    from portfolio_state import DEPLOYMENT_PLAN, RISK_CONTROLS

    df = get_data_from_cache()
    if df is None or len(df) == 0:
        return {"error": "No market data found"}

    df = df.sort("Date")
    latest = df.tail(1).to_dicts()[0]
    nifty_current = latest.get("Nifty50") or 0

    # 52-week high
    nifty_52w = df["Nifty50"].max()
    nifty_52w = nifty_52w if nifty_52w is not None and nifty_52w != 0 else 0
    drawdown_pct = ((nifty_current - nifty_52w) / nifty_52w) * 100 if nifty_52w > 0 else 0

    # Halt rule check
    halt_active = drawdown_pct <= RISK_CONTROLS.nifty_drawdown_halt

    # Tranche eligibility
    tranches_data = []
    for i, tranche in enumerate(DEPLOYMENT_PLAN.tranches):
        triggered = nifty_current <= tranche.nifty_level
        tranches_data.append({
            "id": i + 1,
            "trigger_nifty_level": tranche.nifty_level,
            "triggered": triggered,
            "deployed": tranche.deployed,
            "amount": tranche.amount,
            "asset": tranche.asset,
        })

    eligible_tranches = [t for t in tranches_data if t["triggered"] and not t["deployed"]]
    eligible_to_deploy = not halt_active and len(eligible_tranches) > 0

    max_deploy = (DEPLOYMENT_PLAN.dry_powder_amount * DEPLOYMENT_PLAN.max_single_deploy_pct // 100) if DEPLOYMENT_PLAN.dry_powder_amount else 0

    return {
        "date": str(latest.get("Date", "")),
        "nifty_current": round(nifty_current, 2),
        "nifty_52w_high": round(nifty_52w, 2),
        "drawdown_pct": round(drawdown_pct, 2),
        "halt_rule_active": halt_active,
        "halt_threshold_pct": RISK_CONTROLS.nifty_drawdown_halt,
        "tranches": tranches_data,
        "eligible_to_deploy": eligible_to_deploy,
        "max_deploy_this_tranche": max_deploy,
        "dry_powder": DEPLOYMENT_PLAN.dry_powder_amount,
    }


def get_signal_risk_level() -> dict:
    """Aggregate risk level from all signals + geo context."""
    signals = check_ceasefire_signals()
    df = get_data_from_cache()

    if df is None or len(df) == 0:
        return {"error": "No market data", "risk_level": "UNKNOWN"}

    latest = df.tail(1).to_dicts()[0]
    signals_fired = signals.get("signals_fired", 0)
    current_vix = latest.get("IndiaVIX") or 25  # Default 25 if None

    # Risk mapping
    if signals_fired >= 3 or current_vix > 25:
        risk_level = "LOW"
        description = "Ceasefire signals firing or VIX spiking — war premium unwinding"
    elif signals_fired >= 2:
        risk_level = "MEDIUM"
        description = "Partial ceasefire signals — defensive positioning"
    elif current_vix > 20:
        risk_level = "HIGH"
        description = "Elevated VIX — conflict escalation risk"
    else:
        risk_level = "MEDIUM"
        description = "Baseline portfolio risk — maintain exposure discipline"

    return {
        "date": str(latest.get("Date", "")),
        "risk_level": risk_level,
        "description": description,
        "signals_fired": signals_fired,
        "india_vix": round(current_vix, 2),
        "geo_conflict_intensity": GEO.conflict_intensity,
    }


def get_portfolio_status() -> dict:
    """Full portfolio snapshot from portfolio_state.yaml. Returns allocation + dry powder + constraints."""
    return {
        "corpus_total": ALLOCATION.total_corpus,
        "buckets": {
            "debt": {"amount": ALLOCATION.debt.amount, "target_pct": ALLOCATION.debt.target_percent},
            "gold": {"amount": ALLOCATION.gold.amount, "target_pct": ALLOCATION.gold.target_percent},
            "nps_mf": {"amount": ALLOCATION.nps_mf.amount, "target_pct": ALLOCATION.nps_mf.target_percent},
            "dsp_multi_asset": {"amount": ALLOCATION.dsp_multi_asset.amount, "target_pct": ALLOCATION.dsp_multi_asset.target_percent},
            "liquid_buffer": {"amount": ALLOCATION.liquid_buffer.amount, "target_pct": ALLOCATION.liquid_buffer.target_percent},
        },
        "dry_powder": DEPLOYMENT_PLAN.dry_powder_amount,
        "min_liquid_reserve": DEPLOYMENT_PLAN.min_liquid_reserve,
        "risk_controls": {
            "max_equity_pct": RISK_CONTROLS.max_equity_pct,
            "max_gold_pct": RISK_CONTROLS.max_gold_pct,
            "min_gold_pct": RISK_CONTROLS.min_gold_pct,
        },
        "deployment_log": [
            {
                "date": e.date,
                "amount": e.amount,
                "asset": e.asset,
                "nifty_level": e.nifty_level,
                "notes": e.notes,
            }
            for e in DEPLOYMENT_LOG
        ],
    }


def get_daily_news_digest() -> dict:
    """Fetch and classify today's news from RSS cache (or live RSS if cache is stale)."""
    from news_agent import fetch_news, classify_articles, format_digest, get_market_context

    try:
        articles = fetch_news()
        articles = classify_articles(articles)
        digest = format_digest(articles)
        market = get_market_context()

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "article_count": len(articles),
            "articles": articles,
            "digest": digest,
            "market_context": market or {},
        }
    except Exception as e:
        return {
            "error": f"News fetch failed: {str(e)}",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }


def get_fii_dii_activity() -> dict:
    """Load latest FII/DII flows from SQLite with streak calculation."""
    try:
        from db import load_fii_dii_history
        history = load_fii_dii_history()
    except Exception as e:
        # Fallback if db.py not available — return empty struct
        return {
            "error": f"FII/DII data unavailable: {str(e)}",
            "date": "unknown",
            "fii": {"net": 0, "consecutive_streak": 0, "monthly_total": 0},
            "dii": {"net": 0, "consecutive_streak": 0, "monthly_total": 0},
            "interpretation": "Unknown",
        }

    if not history:
        return {"error": "No FII/DII data found"}

    latest = history[0]  # Most recent

    # Streak calculation
    def calc_streak(records, key, direction="buy"):
        """Count consecutive buy/sell sessions."""
        is_buy = direction == "buy"
        streak = 0
        for rec in records:
            net = getattr(rec, key, 0) or 0
            if (is_buy and net >= 0) or (not is_buy and net < 0):
                streak += 1
            else:
                break
        return streak

    fii_latest_net = getattr(latest, "fii_net", 0) or 0
    dii_latest_net = getattr(latest, "dii_net", 0) or 0

    fii_streak = calc_streak(history, "fii_net", "buy" if fii_latest_net >= 0 else "sell")
    dii_streak = calc_streak(history, "dii_net", "buy" if dii_latest_net >= 0 else "sell")

    # Monthly totals (current month)
    date_iso = getattr(latest, "date_iso", "")
    month_prefix = date_iso[:7] if date_iso else ""
    month_records = [r for r in history if getattr(r, "date_iso", "").startswith(month_prefix)] if month_prefix else []
    fii_monthly = sum(getattr(r, "fii_net", 0) or 0 for r in month_records)
    dii_monthly = sum(getattr(r, "dii_net", 0) or 0 for r in month_records)

    interpretation = (
        "FII selling offset by DII buying" if fii_latest_net < 0 and dii_latest_net > 0
        else "Both buying — strong breadth" if fii_latest_net > 0 and dii_latest_net > 0
        else "Both selling — risk-off" if fii_latest_net < 0 and dii_latest_net < 0
        else "FII-led rally"
    )

    return {
        "date": getattr(latest, "date", "unknown"),
        "date_iso": date_iso,
        "fii": {
            "net": round(fii_latest_net, 2),
            "buy": round(getattr(latest, "fii_buy", 0) or 0, 2),
            "sell": round(getattr(latest, "fii_sell", 0) or 0, 2),
            "consecutive_streak": fii_streak,
            "monthly_total": round(fii_monthly, 2),
        },
        "dii": {
            "net": round(dii_latest_net, 2),
            "buy": round(getattr(latest, "dii_buy", 0) or 0, 2),
            "sell": round(getattr(latest, "dii_sell", 0) or 0, 2),
            "consecutive_streak": dii_streak,
            "monthly_total": round(dii_monthly, 2),
        },
        "interpretation": interpretation,
    }


def get_gold_regime_projection() -> dict:
    """
    Use regime history (30-day window) to compute base probabilities,
    adjust with GEO_CONTEXT conflict intensity, return most likely regime.
    """
    df = get_data_from_cache()
    if df is None or len(df) == 0:
        return {
            "most_likely": "Unknown",
            "confidence": "low",
            "probabilities": {},
            "watch_for": "Insufficient data.",
        }

    # Ensure Date column is parsed
    if df["Date"].dtype != pl.Date:
        df = df.with_columns(pl.col("Date").str.to_date())

    df = df.sort("Date")
    df = df.with_columns([
        ((pl.col("Gold").pct_change() * 100).round(3)).alias("gold_pct"),
        ((pl.col("Nifty50").pct_change() * 100).round(3)).alias("nifty_pct"),
        ((pl.col("DXY").pct_change() * 100).round(3)).alias("dxy_pct"),
    ])

    df = df.filter(
        pl.col("gold_pct").is_not_null() &
        pl.col("nifty_pct").is_not_null() &
        pl.col("dxy_pct").is_not_null()
    )

    # Classify into regimes
    regimes = []
    for row in df.iter_rows(named=True):
        regime, _ = _classify_regime(row["gold_pct"], row["nifty_pct"], row["dxy_pct"])
        regimes.append(regime)

    df = df.with_columns(pl.Series("regime", regimes))

    # Last 30 days for base probabilities
    window = df[-30:] if len(df) >= 30 else df
    regime_freq = Counter(window["regime"])
    total = len(window)

    base_probs = {
        "Liquidity Crunch": regime_freq.get("Liquidity Crunch", 0) / total,
        "War Premium Unwind": regime_freq.get("War Premium Unwind", 0) / total,
        "Macro Headwind": regime_freq.get("Macro Headwind", 0) / total,
        "Equity Rotation": regime_freq.get("Equity Rotation", 0) / total,
        "Secular Continuation": regime_freq.get("Secular Continuation", 0) / total,
    }

    # Adjust with GEO_CONTEXT
    # Map conflict intensity (low/medium/high) to numeric range
    intensity_map = {"low": 0.3, "medium": 0.5, "high": 0.8}
    conflict_intensity = intensity_map.get(GEO.conflict_intensity, 0.5)

    # Higher conflict_intensity → boost Secular Continuation (war premium), lower War Premium Unwind
    adjusted_probs = base_probs.copy()
    intensity_boost = conflict_intensity * 0.15  # Max 15% boost/reduction

    adjusted_probs["Secular Continuation"] = min(base_probs["Secular Continuation"] + intensity_boost, 1.0)
    adjusted_probs["War Premium Unwind"] = max(base_probs["War Premium Unwind"] - intensity_boost, 0.0)

    # Renormalize to sum to 1
    total_adj = sum(adjusted_probs.values())
    if total_adj > 0:
        adjusted_probs = {k: v / total_adj for k, v in adjusted_probs.items()}

    # Most likely regime
    most_likely = max(adjusted_probs, key=adjusted_probs.get)
    max_prob = adjusted_probs[most_likely]

    # Confidence: high if > 35%, medium if > 20%, low otherwise
    if max_prob > 0.35:
        confidence = "high"
    elif max_prob > 0.20:
        confidence = "medium"
    else:
        confidence = "low"

    # Watch_for sentence based on regime
    watch_for_map = {
        "Liquidity Crunch": "Watch for institutional selling panic; consider defensive positions.",
        "War Premium Unwind": "War premium unwinding; gold may face continued selling pressure.",
        "Macro Headwind": "Global risk-off signal; correlation with USD strength likely.",
        "Equity Rotation": "Growth rotation underway; gold typically ranges flat in rotation periods.",
        "Secular Continuation": "Gold continues structural uptrend; maintain hedges.",
    }
    watch_for = watch_for_map.get(most_likely, "Monitor market internals for regime shifts.")

    return {
        "most_likely": most_likely,
        "confidence": confidence,
        "probabilities": {k: round(v, 3) for k, v in adjusted_probs.items()},
        "watch_for": watch_for,
    }


def get_india_adr_quotes() -> dict:
    """
    Fetch live prices for Indian ADRs on NYSE via yfinance.
    Returns prices, prior close, day change % for Banking, IT, Pharma sectors.
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed"}

    ADRs = {
        "Banking": ["HDB", "IBN"],
        "IT":      ["INFY", "WIT"],
        "Pharma":  ["RDY"],
    }

    results = {}
    for sector, tickers in ADRs.items():
        sector_data = []
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                price = info.last_price
                prev  = info.previous_close
                change_pct = round((price - prev) / prev * 100, 2) if prev else None
                sector_data.append({
                    "ticker":      ticker,
                    "price":       round(price, 2),
                    "prev_close":  round(prev, 2),
                    "change_pct":  change_pct,
                    "signal":      (
                        "gap_down_likely" if change_pct is not None and change_pct < -3
                        else "pressure"  if change_pct is not None and change_pct < -1
                        else "positive"  if change_pct is not None and change_pct > 1
                        else "flat"
                    ),
                })
            except Exception as e:
                sector_data.append({"ticker": ticker, "error": str(e)})
        results[sector] = sector_data

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time_ist": datetime.now().strftime("%H:%M IST"),
        "adrs": results,
        "source": "yfinance",
    }


def _scrape_panchang(date_str: str) -> dict:
    """Scrape a single day's panchang from ProKerala. Returns raw dict."""
    import requests
    from bs4 import BeautifulSoup

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    url = f"https://www.prokerala.com/astrology/panchang/?date={date_str}&tz=Asia%2FKolkata"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    lines = [l.strip() for l in soup.get_text(separator="\n").split("\n") if l.strip()]

    def extract(key):
        for i, line in enumerate(lines):
            if line == key:
                for j in range(i + 1, min(i + 5, len(lines))):
                    v = lines[j]
                    if v and v not in ("-", key):
                        return v
        return None

    return {
        "date": date_str,
        "display_date": dt.strftime("%d %B %Y"),
        "weekday": dt.strftime("%A"),
        "location": "Ujjain, Madhya Pradesh, India",
        "tithi":      extract("Tithi"),
        "nakshatra":  extract("Nakshatra"),
        "yoga":       extract("Yoga"),
        "karana":     extract("Karana"),
        "vara":       extract("Vara"),
        "chandra_rasi": extract("Chandra Rasi"),
        "sunrise":    extract("Sunrise"),
        "sunset":     extract("Sunset"),
        "moonrise":   extract("Moonrise"),
        "moonset":    extract("Moonset"),
        "ayana":      extract("Ayana"),
        "ritu":       extract("Drik Ritu"),
        "vikram_samvat": extract("Vikram Samvat"),
        "shaka_samvat":  extract("Shaka Samvat"),
        "paksha":     extract("Purnimanta"),
        "festivals":  extract("Festivals & Vrats"),
        "inauspicious": {
            "rahu_kaal":  extract("Rahu"),
            "yamaganda":  extract("Yamaganda"),
            "gulika":     extract("Gulika"),
            "dur_muhurat": extract("Dur Muhurat"),
            "varjyam":    extract("Varjyam"),
        },
        "auspicious": {
            "abhijit_muhurat": extract("Abhijit Muhurat"),
            "amrit_kaal":      extract("Amrit Kaal"),
            "brahma_muhurat":  extract("Brahma Muhurat"),
        },
        "source": "prokerala.com",
        "url": url,
    }


def _build_panchang_note(p: dict) -> str:
    """Build Obsidian markdown note content from a panchang dict."""
    dt = datetime.strptime(p["date"], "%Y-%m-%d")
    festivals_str = p.get("festivals") or "None"
    ia = p.get("inauspicious", {})
    au = p.get("auspicious", {})

    return f"""---
tags:
  - panchang
  - daily
  - ujjain
  - hindu-calendar
  - year-{dt.strftime('%Y')}
date: {p['date']}
weekday: {p['weekday']}
tithi: "{p.get('tithi') or ''}"
nakshatra: "{p.get('nakshatra') or ''}"
yoga: "{p.get('yoga') or ''}"
karana: "{p.get('karana') or ''}"
vara: "{p.get('vara') or ''}"
vikram_samvat: "{p.get('vikram_samvat') or ''}"
shaka_samvat: "{p.get('shaka_samvat') or ''}"
paksha: "{p.get('paksha') or ''}"
ritu: "{p.get('ritu') or ''}"
festivals: "{festivals_str}"
ayana: "{p.get('ayana') or ''}"
chandra_rasi: "{p.get('chandra_rasi') or ''}"
source: prokerala.com
location: Ujjain
cached: true
---

# Panchang — {p['display_date']} ({p['weekday']})

> Source: [ProKerala]({p['url']}) | Location: Ujjain (IST reference)

## Pancha Anga (Five Limbs)

| Element | Value |
|---------|-------|
| **Tithi** | {p.get('tithi') or '—'} |
| **Nakshatra** | {p.get('nakshatra') or '—'} |
| **Yoga** | {p.get('yoga') or '—'} |
| **Karana** | {p.get('karana') or '—'} |
| **Vara** | {p.get('vara') or '—'} |
| **Chandra Rasi** | {p.get('chandra_rasi') or '—'} |

## Sun & Moon

| | Time |
|--|------|
| Sunrise | {p.get('sunrise') or '—'} |
| Sunset | {p.get('sunset') or '—'} |
| Moonrise | {p.get('moonrise') or '—'} |
| Moonset | {p.get('moonset') or '—'} |

## Calendar

| | |
|--|--|
| Vikram Samvat | {p.get('vikram_samvat') or '—'} |
| Shaka Samvat | {p.get('shaka_samvat') or '—'} |
| Paksha | {p.get('paksha') or '—'} |
| Ayana | {p.get('ayana') or '—'} |
| Ritu | {p.get('ritu') or '—'} |
| Festivals | {festivals_str} |

## Auspicious Timings ✅

| | |
|--|--|
| Abhijit Muhurat | {au.get('abhijit_muhurat') or '—'} |
| Amrit Kaal | {au.get('amrit_kaal') or '—'} |
| Brahma Muhurat | {au.get('brahma_muhurat') or '—'} |

## Inauspicious Timings ❌

| | |
|--|--|
| Rahu Kaal | {ia.get('rahu_kaal') or '—'} |
| Yamaganda | {ia.get('yamaganda') or '—'} |
| Gulika | {ia.get('gulika') or '—'} |
| Dur Muhurat | {ia.get('dur_muhurat') or '—'} |
| Varjyam | {ia.get('varjyam') or '—'} |
"""


def _vault_note_exists(note_path: str) -> bool:
    """Check if a vault note exists via local-mpc vault_read."""
    import subprocess, json
    try:
        result = subprocess.run(
            ["local-mpc", "call", "vault_read", json.dumps({"note": note_path})],
            capture_output=True, text=True, timeout=10
        )
        return "not found" not in result.stdout.lower() and result.returncode == 0
    except Exception:
        return False


def _vault_write_note(note_path: str, content: str) -> None:
    """Write a note to vault via local-mpc."""
    import subprocess, json
    payload = json.dumps({"note": note_path, "content": content, "overwrite": True})
    subprocess.run(["local-mpc", "call", "vault_write", payload],
                   capture_output=True, timeout=10)


def get_panchang_today(date_str: str = None) -> dict:
    """Return panchang for today + tomorrow, using vault cache when available.

    Cache strategy:
    - Check vault for Daily/panchang_YYYY-MM-DD before scraping
    - Always fetch both today AND tomorrow (tithis span midnight)
    - Write missing dates to vault; skip dates already cached

    Args:
        date_str: Base date in YYYY-MM-DD (defaults to today IST).

    Returns:
        dict with 'today' and 'tomorrow' panchang dicts, plus 'cache_hits'.
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    tomorrow_str = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    dates = [date_str, tomorrow_str]
    results = {}
    cache_hits = []

    for d in dates:
        note_path = f"Daily/panchang_{d}"
        if _vault_note_exists(note_path):
            # Cache hit — read from vault
            import subprocess, json
            try:
                r = subprocess.run(
                    ["local-mpc", "call", "vault_read", json.dumps({"note": note_path})],
                    capture_output=True, text=True, timeout=10
                )
                results[d] = {"date": d, "source": "vault_cache", "vault_path": note_path,
                              "raw": r.stdout[:500]}
                cache_hits.append(d)
            except Exception:
                results[d] = {"date": d, "source": "vault_cache", "vault_path": note_path}
                cache_hits.append(d)
        else:
            # Cache miss — scrape and write to vault
            try:
                panchang = _scrape_panchang(d)
                content = _build_panchang_note(panchang)
                _vault_write_note(note_path, content)
                panchang["vault_path"] = note_path
                panchang["source"] = "prokerala.com (scraped)"
                results[d] = panchang
            except Exception as e:
                results[d] = {"date": d, "error": str(e)}

    return {
        "today": results[date_str],
        "tomorrow": results[tomorrow_str],
        "cache_hits": cache_hits,
        "fetched": [d for d in dates if d not in cache_hits],
    }
