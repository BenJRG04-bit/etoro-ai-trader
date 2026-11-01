"""Fail-closed historical-data routing for multi-asset research.

Broker symbols are not assumed to equal public data provider symbols.
No network requests or trades are made by this module.
"""
from types import MappingProxyType
from multi_asset_universe import CRYPTO, FOREX, COMMODITIES, COMMODITY_ETFS, BOND_ETFS

# Known Yahoo-style history symbols. These are mapping CANDIDATES, not a
# claim that prices are validated or comparable with eToro executable quotes.
PROVIDER_SYMBOL_CANDIDATES = MappingProxyType({
    **{s: s + "-USD" for s in CRYPTO},
    **{s: s[:3] + s[3:] + "=X" for s in FOREX if s.endswith("USD")},
    "USDJPY": "JPY=X", "EURGBP": "EURGBP=X",
    "USDCAD": "CAD=X", "USDCHF": "CHF=X",
    **{s: s for s in COMMODITY_ETFS + BOND_ETFS},
})
REQUIRES_INSTRUMENT_VERIFICATION = frozenset(COMMODITIES)
EXPECTED_PRICE_UNITS = MappingProxyType({
    **{s: "USD_per_crypto_unit" for s in CRYPTO},
    **{s: "quote_currency_per_base_currency" for s in FOREX},
    **{s: "USD_per_ETF_share" for s in COMMODITY_ETFS + BOND_ETFS},
})


def research_data_plan(symbol):
    if symbol in REQUIRES_INSTRUMENT_VERIFICATION:
        return {"symbol": symbol, "status": "BLOCKED_MAPPING_UNVERIFIED",
                "broker_orders_allowed": False,
                "reason": "Direct commodity eToro contract and public proxy not verified"}
    if symbol not in PROVIDER_SYMBOL_CANDIDATES:
        raise ValueError("Symbol is not in the verified multi-asset research catalogue")
    return {"symbol": symbol,
            "provider_symbol_candidate": PROVIDER_SYMBOL_CANDIDATES[symbol],
            "expected_price_unit": EXPECTED_PRICE_UNITS[symbol],
            "status": "CANDIDATE_NOT_VALIDATED",
            "history_validated": False, "execution_quote_comparable": False,
            "broker_orders_allowed": False}


def validate_research_history(symbol, dates, closes, *, minimum_rows=120):
    """Validate shape and chronology; does NOT certify source provenance."""
    import math
    from datetime import date
    plan = research_data_plan(symbol)
    if plan["status"] != "CANDIDATE_NOT_VALIDATED":
        raise ValueError("Unverified instrument mapping")
    if len(dates) != len(closes) or len(dates) < minimum_rows:
        raise ValueError("Missing or insufficient history")
    previous = None
    for day, price in zip(dates, closes):
        parsed = date.fromisoformat(day)
        if previous is not None and parsed <= previous:
            raise ValueError("Dates are not strictly increasing")
        if not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
            raise ValueError("Invalid price")
        previous = parsed
    return {"symbol": symbol, "validated_rows": len(closes),
            "date_start": dates[0], "date_end": dates[-1],
            "shape_validated": True, "provider_provenance_validated": False,
            "execution_quote_comparable": False, "broker_orders_allowed": False}
