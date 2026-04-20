"""
portfolio_state.py — Loader only. All values live in PORTFOLIO_STATE.md (vault).

Edit values in:
    $VAULT_PATH/Documentation/market-intel/PORTFOLIO_STATE.md
    (edit only the yaml code block inside that note)

Sections loaded:
    Owner           — identity + monthly burn
    FundComposition — DSP_COMPOSITION (constituent breakdown)
    Allocation      — 5 buckets (total_corpus is computed @property)
    RiskControls    — hard ceilings + halt thresholds
    DeploymentPlan  — dry powder, tranches, reserve floor
    FundSelectionRules — which fund to buy based on gold behaviour
    CeasefireConfig — 4 signals + confirmation threshold
    GoldTrimTrigger — compound condition for trimming gold
    GeoContext      — live conflict state
    TICKERS         — yfinance symbols
    ADR_SECTORS     — India ADR tickers by sector
    WATCHLIST       — post-war recovery entry zones
    DEPLOYMENT_LOG  — immutable history; append only

See also:
    wiki/WIKI_EQUITY_EXPANSION_2026.md — 3-stage DSP-to-Nifty rebalancing plan (April 2026+)
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

import os
_VAULT_PATH = os.environ.get("VAULT_PATH", str(Path.home() / "workspace/claude_documents"))
_MD_PATH = Path(_VAULT_PATH) / "Documentation/market-intel/PORTFOLIO_STATE.md"


def _load() -> dict:
    """Extract the first ```yaml``` code block from the vault .md note and load it."""
    text = _MD_PATH.read_text()
    # Extract content between first ```yaml and closing ```
    start = text.index("```yaml\n") + len("```yaml\n")
    end = text.index("\n```", start)
    return yaml.safe_load(text[start:end])


_cfg = _load()


# ── Owner ─────────────────────────────────────────────────────────────────────

@dataclass
class Owner:
    name: str
    status: str
    monthly_expense: int
    last_employer_exit: str
    last_epf_transaction: str


# ── Allocation ────────────────────────────────────────────────────────────────

@dataclass
class Bucket:
    label: str
    target_percent: float
    amount: int


@dataclass
class FundComposition:
    """Internal constituent breakdown of a multi-asset fund (approximate %)."""
    debt_pct:         float
    india_eq_pct:     float
    global_eq_pct:    float
    commodities_pct:  float

    def amount_breakdown(self, total: int) -> dict:
        """Return rupee breakdown given a total fund amount."""
        return {
            "debt":        int(total * self.debt_pct        / 100),
            "india_eq":    int(total * self.india_eq_pct    / 100),
            "global_eq":   int(total * self.global_eq_pct   / 100),
            "commodities": int(total * self.commodities_pct / 100),
        }


@dataclass
class Allocation:
    debt:           Bucket
    gold:           Bucket
    nps_mf:         Bucket
    dsp_multi_asset: Bucket
    liquid_buffer:  Bucket

    @property
    def hybrid_growth_total(self) -> int:
        """Combined NPS+MF + DSP Multi Asset — used for equity ceiling check."""
        return self.nps_mf.amount + self.dsp_multi_asset.amount

    @property
    def total_corpus(self) -> int:
        return (
            self.debt.amount
            + self.gold.amount
            + self.nps_mf.amount
            + self.dsp_multi_asset.amount
            + self.liquid_buffer.amount
        )


# ── Risk Controls ─────────────────────────────────────────────────────────────

@dataclass
class RiskControls:
    max_equity_pct: float
    max_gold_pct: float
    min_gold_pct: float
    nifty_drawdown_halt: float
    portfolio_loss_alert: float


# ── Deployment ────────────────────────────────────────────────────────────────

@dataclass
class Tranche:
    nifty_level: int
    amount: int
    asset: str
    deployed: bool = False
    notes: str = ""


@dataclass
class DeploymentPlan:
    dry_powder_amount: int
    min_liquid_reserve: int
    max_single_deploy_pct: int
    od_facility_amount: int
    od_interest_rate_pct: float
    tranches: list[Tranche] = field(default_factory=list)


# ── Fund Selection Rules ──────────────────────────────────────────────────────

@dataclass
class FundSelectionRules:
    nifty_threshold: float
    nifty_drop_min_pct: float
    gold_falling_threshold: float
    gold_flat_threshold: float
    multi_asset_fund: str
    flexicap_fund: str


# ── Ceasefire Signals ─────────────────────────────────────────────────────────

@dataclass
class CeasefireConfig:
    oil_drop_pct: float
    gold_rise_pct: float
    vix_below: float
    nifty_gain_pct: float
    min_signals_required: int


# ── Gold Trim Trigger ─────────────────────────────────────────────────────────

@dataclass
class GoldTrimTrigger:
    veto_gold_drop_pct: float
    veto_nifty_drop_pct: float
    veto_dxy_min_change: float
    tips_yield_rise_bp: float
    dxy_rise_pct: float
    rsi_weekly_overbought: float
    days_below_50dma: int
    nifty_rally_from_low_pct: float
    nifty_rally_days: int
    vix_below_sustained: float
    vix_sustained_days: int
    tranche_1_pct: float
    tranche_2_pct: float
    max_total_trim_pct: float
    min_gold_allocation_pct: float
    seasonal_no_trim_start: str
    seasonal_no_trim_end: str
    price_floor_veto_usd: float
    pre_war_gold_usd: float


# ── Geopolitical Context ──────────────────────────────────────────────────────

@dataclass
class GeoContext:
    conflict_name: str
    conflict_intensity: str
    war_duration_estimate: str
    short_war_probability: float
    last_updated: str
    notes: str


# ── Watchlist ─────────────────────────────────────────────────────────────────

@dataclass
class WatchlistEntry:
    name: str
    ticker: str
    wave: str
    zone_low: float
    zone_high: float
    note: str


# ── Deployment Log ─────────────────────────────────────────────────────────────

@dataclass
class DeploymentLogEntry:
    date: str
    amount: int
    asset: str
    nifty_level: int
    notes: str


# ── Builders ─────────────────────────────────────────────────────────────────

def _build_allocation(d: dict) -> Allocation:
    return Allocation(
        debt=Bucket(**d["debt"]),
        gold=Bucket(**d.get("gold", d.get("hard_assets", {}))),
        nps_mf=Bucket(**d["nps_mf"]),
        dsp_multi_asset=Bucket(**d["dsp_multi_asset"]),
        liquid_buffer=Bucket(**d["liquid_buffer"]),
    )


def _build_deployment_plan(d: dict) -> DeploymentPlan:
    tranches = [Tranche(**t) for t in d.pop("tranches", [])]
    return DeploymentPlan(**d, tranches=tranches)


def _build_adr_sectors(d: dict) -> dict[str, list[tuple[str, str]]]:
    return {sector: [tuple(pair) for pair in pairs] for sector, pairs in d.items()}


# ── Singleton instances (import these) ───────────────────────────────────────

OWNER            = Owner(**_cfg["owner"])
DSP_COMPOSITION  = FundComposition(**_cfg["dsp_composition"])
ALLOCATION       = _build_allocation(_cfg["allocation"])
RISK_CONTROLS    = RiskControls(**_cfg["risk_controls"])
DEPLOYMENT_PLAN  = _build_deployment_plan(dict(_cfg["deployment_plan"]))
FUND_SELECTION   = FundSelectionRules(**_cfg["fund_selection"])
CEASEFIRE        = CeasefireConfig(**_cfg["ceasefire"])
GOLD_TRIM        = GoldTrimTrigger(**_cfg["gold_trim"])
GEO              = GeoContext(**_cfg["geo_context"])

TICKERS: dict[str, str]                         = _cfg["tickers"]
ADR_SECTORS: dict[str, list[tuple[str, str]]]   = _build_adr_sectors(_cfg["adr_sectors"])
WATCHLIST: list[WatchlistEntry]                 = [WatchlistEntry(**e) for e in _cfg["watchlist"]]
DEPLOYMENT_LOG: list[DeploymentLogEntry]        = [DeploymentLogEntry(**e) for e in _cfg["deployment_log"]]
