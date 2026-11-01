"""Verified eToro symbol research catalogue, not a trading authorization.

Instrument identity/eligibility observed 2026-11-01. Eligibility, quote freshness,
settlement, fees and order minimums must be rechecked at execution time.
"""
from types import MappingProxyType

CRYPTO = ("BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "LTC")
FOREX = ("EURUSD", "GBPUSD", "USDJPY", "EURGBP", "AUDUSD", "USDCAD", "USDCHF")
COMMODITIES = ("GOLD", "SILVER", "OIL", "NATGAS", "PLATINUM")
COMMODITY_ETFS = ("GLD", "SLV", "USO", "UNG", "XLE", "GDX")
BOND_ETFS = ("TLT", "IEF")
GROUPS = MappingProxyType({
    "crypto": CRYPTO, "forex": FOREX, "commodities": COMMODITIES,
    "commodity_etfs": COMMODITY_ETFS, "bond_etfs": BOND_ETFS,
})
ALL_NEW_SYMBOLS = tuple(s for group in GROUPS.values() for s in group)
# Brokerage-reported minimum EXPOSURE, not minimum cash deposit or recommendation.
MIN_EXPOSURE_USD = MappingProxyType({
    **{s: 1000 for s in FOREX + COMMODITIES},
    **{s: 10 for s in CRYPTO + COMMODITY_ETFS + BOND_ETFS},
})


def multi_asset_research_plan():
    return {
        "mode": "MULTI_ASSET_RESEARCH_ONLY",
        "groups": {name: list(symbols) for name, symbols in GROUPS.items()},
        "minimum_reported_exposure_usd": dict(MIN_EXPOSURE_USD),
        "additional_symbols": len(ALL_NEW_SYMBOLS),
        "requires_asset_specific_data_adapters": True,
        "requires_trading_hours_and_cost_models": True,
        "requires_chronological_holdout_validation": True,
        "data_collection_implemented": False,
        "model_training_implemented_for_new_assets": False,
        "broker_orders_allowed": False,
        "demo_trading_approved": False,
        "live_trading_approved": False,
        "notes": ("Current public daily-price adapter supports equities/ETFs only. "
                  "Crypto, FX and direct commodities require separate verified history "
                  "sources and instrument-specific price/cost handling. Never assume "
                  "Yahoo symbols map directly to eToro symbols or that 24/7 trading "
                  "applies to every market. No paid AI API required."),
    }
