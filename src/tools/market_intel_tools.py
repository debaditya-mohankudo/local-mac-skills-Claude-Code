"""
market_intel_tools.py
---------------------
MCP tool handlers for gold regime history and projection.

Reads market price history from the parquet cache at:
    ~/Documents/claude_cache_data/market-intel/parquet/market_prices.parquet

Columns expected: date, gold, nifty50, dxy (lowercase)

Registered as domain 'market' → mcp__local-mac__market__<action>
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

_PARQUET = Path.home() / "Documents/claude_cache_data/market-intel/parquet/market_prices.parquet"

# ── Regime classification ──────────────────────────────────────────────────────

def _classify_regime(gold_chg: float, nifty_chg: float, dxy_chg: float) -> tuple[str, str]:
    """
    Classify a single day into one of 5 regimes.

    Returns: (regime_name, flag)
      flag "X" = Gate 0 veto (sharp crash day — do not trim)
      flag "T" = trim candidate
      flag ""  = neutral
    """
    if gold_chg is None or nifty_chg is None or dxy_chg is None:
        return "Unknown", ""

    flag = "X" if (gold_chg < -1.5 or nifty_chg < -2.0) else ""

    if gold_chg < 0 and nifty_chg < 0 and dxy_chg > 0:
        return "Liquidity Crunch", flag

    if gold_chg < 0 and nifty_chg > 0 and abs(dxy_chg) <= 0.3:
        return "War Premium Unwind", flag if flag == "X" else "T"

    if gold_chg < 0 and dxy_chg > 0:
        return "Macro Headwind", flag

    if gold_chg <= 0.1 and nifty_chg > 0 and abs(dxy_chg) <= 0.3:
        return "Equity Rotation", flag if flag == "X" else "T"

    return "Secular Continuation", flag


def _load_cache() -> pd.DataFrame | None:
    """Load parquet cache; return None on error."""
    if not _PARQUET.exists():
        return None
    try:
        df = pd.read_parquet(_PARQUET)
        # normalise column names to lowercase
        df.columns = [c.lower() for c in df.columns]
        # ensure date column is string-sortable
        df = df.sort_values("date").reset_index(drop=True)
        return df
    except Exception:
        return None


def _add_regime_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["gold_pct"]  = df["gold"].pct_change() * 100
    df["nifty_pct"] = df["nifty50"].pct_change() * 100
    df["dxy_pct"]   = df["dxy"].pct_change() * 100
    df = df.dropna(subset=["gold_pct", "nifty_pct", "dxy_pct"]).reset_index(drop=True)
    regimes, flags = zip(*[
        _classify_regime(r.gold_pct, r.nifty_pct, r.dxy_pct)
        for r in df.itertuples()
    ]) if len(df) else ([], [])
    df["regime"] = list(regimes)
    df["flag"]   = list(flags)
    return df


# ── Tool handlers ──────────────────────────────────────────────────────────────

def handle_gold_regime_history() -> dict:
    """
    Gold regime history from parquet cache.

    Returns current regime, streak, 5-day momentum, recent 5 days,
    regime distribution, and Gate 0 / trim candidate counts.
    """
    df = _load_cache()
    if df is None or len(df) == 0:
        return {
            "current_regime": "Unknown",
            "streak_days": 0,
            "momentum_5d": {"gold": 0.0, "nifty": 0.0, "dxy": 0.0},
            "recent_5": [],
            "regime_counts": {},
            "gate0_veto_days": 0,
            "trim_candidate_days": 0,
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
        }

    df = _add_regime_cols(df)

    current_regime = df["regime"].iloc[-1]

    # streak
    streak = 1
    for reg in reversed(df["regime"].iloc[:-1].tolist()):
        if reg == current_regime:
            streak += 1
        else:
            break

    last5 = df.tail(5)
    gold_mom  = round(float(last5["gold_pct"].mean()),  3)
    nifty_mom = round(float(last5["nifty_pct"].mean()), 3)
    dxy_mom   = round(float(last5["dxy_pct"].mean()),   3)

    recent_5 = []
    for row in last5.itertuples():
        recent_5.insert(0, {
            "date":      str(row.date),
            "gold_pct":  round(row.gold_pct,  2),
            "nifty_pct": round(row.nifty_pct, 2),
            "dxy_pct":   round(row.dxy_pct,   2),
            "regime":    row.regime,
            "flag":      row.flag,
        })

    return {
        "current_regime":    current_regime,
        "streak_days":       int(streak),
        "momentum_5d":       {"gold": gold_mom, "nifty": nifty_mom, "dxy": dxy_mom},
        "recent_5":          recent_5,
        "regime_counts":     dict(Counter(df["regime"])),
        "gate0_veto_days":   int((df["flag"] == "X").sum()),
        "trim_candidate_days": int((df["flag"] == "T").sum()),
        "last_updated":      str(df["date"].iloc[-1]),
    }


def handle_gold_regime_projection() -> dict:
    """
    Next-regime probability estimate from 30-day regime frequency,
    adjusted for geo-conflict intensity (read from vault if available,
    else defaults to 'high').

    Returns most_likely regime, confidence, probability table, watch_for.
    """
    df = _load_cache()
    if df is None or len(df) == 0:
        return {
            "most_likely": "Unknown",
            "confidence": "low",
            "probabilities": {},
            "watch_for": "Insufficient data.",
        }

    df = _add_regime_cols(df)
    window = df.tail(30)
    total  = len(window)

    regime_names = [
        "Liquidity Crunch", "War Premium Unwind", "Macro Headwind",
        "Equity Rotation", "Secular Continuation",
    ]
    base_probs = {r: window["regime"].tolist().count(r) / total for r in regime_names}

    # geo-conflict adjustment
    conflict_intensity = _geo_conflict_intensity()
    intensity_map = {"low": 0.3, "medium": 0.5, "high": 0.8}
    intensity = intensity_map.get(conflict_intensity, 0.5)
    boost = intensity * 0.15

    adj = dict(base_probs)
    adj["Secular Continuation"] = min(adj["Secular Continuation"] + boost, 1.0)
    adj["War Premium Unwind"]   = max(adj["War Premium Unwind"]   - boost, 0.0)

    total_adj = sum(adj.values()) or 1.0
    adj = {k: v / total_adj for k, v in adj.items()}

    most_likely = max(adj, key=adj.get)
    max_prob    = adj[most_likely]
    confidence  = "high" if max_prob > 0.35 else ("medium" if max_prob > 0.20 else "low")

    watch_for_map = {
        "Liquidity Crunch":    "Watch for institutional selling panic; maintain defensive positions.",
        "War Premium Unwind":  "Peace talk progress + oil drop could accelerate unwind toward $4,200.",
        "Macro Headwind":      "Global risk-off; DXY strength likely to weigh on gold further.",
        "Equity Rotation":     "Growth rotation; gold may range flat — avoid new entries.",
        "Secular Continuation":"Structural uptrend intact; hold and add on dips.",
    }

    return {
        "most_likely":   most_likely,
        "confidence":    confidence,
        "probabilities": {k: round(v, 3) for k, v in adj.items()},
        "watch_for":     watch_for_map.get(most_likely, "Monitor market internals."),
        "conflict_intensity": conflict_intensity,
    }


def _geo_conflict_intensity() -> str:
    """Try to read conflict_intensity from vault PORTFOLIO_STATE.md; default 'high'."""
    try:
        import yaml
        from config import config
        # Resolved from config, not rebuilt here: the vault lives under iCloud and
        # is overridable via VAULT_PATH, so a second hardcoded guess silently
        # returns the default instead of reading the real file.
        md = config.vault_path / "Documentation/market-intel/PORTFOLIO_STATE.md"
        if not md.exists():
            return "high"
        text = md.read_text()
        start = text.index("```yaml\n") + len("```yaml\n")
        end   = text.index("\n```", start)
        cfg   = yaml.safe_load(text[start:end])
        return cfg.get("GeoContext", {}).get("conflict_intensity", "high")
    except Exception:
        return "high"
