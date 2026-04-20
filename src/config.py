"""
config.py — Adapter layer between portfolio_state.py and tools.py.

Exports the same names tools.py expects. All values sourced from portfolio_state.py (which loads portfolio_state.yaml from vault).
"""

import os
from pathlib import Path

import portfolio_state as _ps


# Module-level singleton values for vault location.
VAULT_PATH = Path(
    os.environ.get("VAULT_PATH", str(Path.home() / "workspace" / "claude_documents"))
).expanduser()
VAULT_DAILY_DIR = VAULT_PATH / "Daily"


PROJECT = {
    "owner":           _ps.OWNER.name,
    "status":          _ps.OWNER.status,
    "monthly_expense": _ps.OWNER.monthly_expense,
}

ALLOCATION = {
    "debt": {
        "label":  _ps.ALLOCATION.debt.label,
        "target": _ps.ALLOCATION.debt.target_percent / 100.0,
        "amount": _ps.ALLOCATION.debt.amount,
    },
    "gold": {
        "label":  _ps.ALLOCATION.gold.label,
        "target": _ps.ALLOCATION.gold.target_percent / 100.0,
        "amount": _ps.ALLOCATION.gold.amount,
    },
    "nps_mf": {
        "label":  _ps.ALLOCATION.nps_mf.label,
        "target": _ps.ALLOCATION.nps_mf.target_percent / 100.0,
        "amount": _ps.ALLOCATION.nps_mf.amount,
    },
    "dsp_multi_asset": {
        "label":  _ps.ALLOCATION.dsp_multi_asset.label,
        "target": _ps.ALLOCATION.dsp_multi_asset.target_percent / 100.0,
        "amount": _ps.ALLOCATION.dsp_multi_asset.amount,
    },
    "liquid_buffer": {
        "label":  _ps.ALLOCATION.liquid_buffer.label,
        "target": _ps.ALLOCATION.liquid_buffer.target_percent / 100.0,
        "amount": _ps.ALLOCATION.liquid_buffer.amount,
    },
}

# Computed — never manually stored
TOTAL_CORPUS = _ps.ALLOCATION.total_corpus

DEPLOYMENT_PLAN = {
    "dry_powder_amount":     _ps.DEPLOYMENT_PLAN.dry_powder_amount,
    "min_liquid_reserve":    _ps.DEPLOYMENT_PLAN.min_liquid_reserve,
    "max_single_deploy_pct": _ps.DEPLOYMENT_PLAN.max_single_deploy_pct,
}

# deployed=True tranches are included so tools can show full tranche history.
# check_deployment_triggers() skips them in the actionable count.
DEPLOYMENT_TRIGGERS = {
    t.nifty_level: {
        "amount":   t.amount,
        "asset":    t.asset,
        "deployed": t.deployed,
        "notes":    t.notes,
    }
    for t in _ps.DEPLOYMENT_PLAN.tranches
}

CEASEFIRE_SIGNALS = {
    "oil_drop_pct":         _ps.CEASEFIRE.oil_drop_pct,
    "gold_rise_pct":        _ps.CEASEFIRE.gold_rise_pct,
    "vix_below":            _ps.CEASEFIRE.vix_below,
    "nifty_gain_pct":       _ps.CEASEFIRE.nifty_gain_pct,
    "min_signals_required": _ps.CEASEFIRE.min_signals_required,
}

RISK_CONTROLS = {
    "max_equity_pct":       _ps.RISK_CONTROLS.max_equity_pct / 100.0,
    "max_gold_pct":         _ps.RISK_CONTROLS.max_gold_pct / 100.0,
    "nifty_drawdown_halt":  _ps.RISK_CONTROLS.nifty_drawdown_halt,
    "portfolio_loss_alert": _ps.RISK_CONTROLS.portfolio_loss_alert,
}

FUND_SELECTION_RULES = {
    "nifty_threshold":        _ps.FUND_SELECTION.nifty_threshold,
    "nifty_drop_min_pct":     _ps.FUND_SELECTION.nifty_drop_min_pct,
    "gold_falling_threshold": _ps.FUND_SELECTION.gold_falling_threshold,
    "gold_flat_threshold":    _ps.FUND_SELECTION.gold_flat_threshold,
    "multi_asset_fund":       _ps.FUND_SELECTION.multi_asset_fund,
    "flexicap_fund":          _ps.FUND_SELECTION.flexicap_fund,
}

GOLD_TRIM_TRIGGER = {
    # Gate 0 — liquidity crunch veto
    "veto_gold_drop_pct":       _ps.GOLD_TRIM.veto_gold_drop_pct,
    "veto_nifty_drop_pct":      _ps.GOLD_TRIM.veto_nifty_drop_pct,
    "veto_dxy_min_change":      _ps.GOLD_TRIM.veto_dxy_min_change,
    # Gate 2 — macro headwind
    "tips_yield_rise_bp":       _ps.GOLD_TRIM.tips_yield_rise_bp,
    "dxy_rise_pct":             _ps.GOLD_TRIM.dxy_rise_pct,
    # Gate 3 — technical
    "rsi_weekly_overbought":    _ps.GOLD_TRIM.rsi_weekly_overbought,
    "days_below_50dma":         _ps.GOLD_TRIM.days_below_50dma,
    # Gate 4 — equity rotation (primary trigger)
    "nifty_rally_from_low_pct": _ps.GOLD_TRIM.nifty_rally_from_low_pct,
    "nifty_rally_days":         _ps.GOLD_TRIM.nifty_rally_days,
    "vix_below_sustained":      _ps.GOLD_TRIM.vix_below_sustained,
    "vix_sustained_days":       _ps.GOLD_TRIM.vix_sustained_days,
    # Trim sizing
    "tranche_1_pct":            _ps.GOLD_TRIM.tranche_1_pct,
    "tranche_2_pct":            _ps.GOLD_TRIM.tranche_2_pct,
    "max_total_trim_pct":       _ps.GOLD_TRIM.max_total_trim_pct,
    # Seasonal veto
    "seasonal_no_trim_start":   _ps.GOLD_TRIM.seasonal_no_trim_start,
    "seasonal_no_trim_end":     _ps.GOLD_TRIM.seasonal_no_trim_end,
    # Reference
    "pre_war_gold_usd":         _ps.GOLD_TRIM.pre_war_gold_usd,
}

GEO_CONTEXT = {
    "conflict_name":         _ps.GEO.conflict_name,
    "conflict_intensity":    _ps.GEO.conflict_intensity,
    "war_duration_estimate": _ps.GEO.war_duration_estimate,
    "short_war_probability": _ps.GEO.short_war_probability,
    "last_updated":          _ps.GEO.last_updated,
    "notes":                 _ps.GEO.notes,
}

TICKERS = _ps.TICKERS
ADR_SECTORS = _ps.ADR_SECTORS
