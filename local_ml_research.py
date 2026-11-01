"""Zero-paid-API chronological machine-learning experiment. Never sends orders."""
import json
from math import exp, isfinite, log
from statistics import mean, pstdev

from historical_prices import WATCHLIST, fetch_daily_closes

SAFE = {"research_only": True, "orders_allowed": False,
        "demo_trading_approved": False, "live_trading_approved": False}
VERSION = "local-logistic-v1"
LOOKBACK = 60
COST_PER_SIDE = 0.0025
EXPOSURE = 0.05


def _features(prices, t):
    """Only data through t; target is the t->t+1 return."""
    p = prices[t]
    recent = [prices[i] / prices[i-1] - 1 for i in range(t-19, t+1)]
    return (max(-3, min(3, (p / prices[t-5] - 1) * 10)),
            max(-3, min(3, (p / prices[t-20] - 1) * 5)),
            max(-3, min(3, (p / mean(prices[t-19:t+1]) - 1) * 10)),
            max(-3, min(3, pstdev(recent) * 30)),
            max(-3, min(3, (p / max(prices[t-59:t+1]) - 1) * 10)))


def _sigmoid(z):
    return 1 / (1 + exp(-max(-30, min(30, z))))


def _fit(samples, epochs=80, rate=0.05, penalty=0.02):
    weights = [0.0] * 6
    for _ in range(epochs):
        gradient = [0.0] * 6
        for features, target in samples:
            row = (1.0,) + features
            delta = _sigmoid(sum(a*b for a, b in zip(weights, row))) - target
            for j in range(6):
                gradient[j] += delta * row[j]
        for j in range(6):
            gradient[j] = gradient[j] / len(samples) + (penalty * weights[j] if j else 0)
            weights[j] -= rate * gradient[j]
    return weights


def evaluate_local_model(closes, *, train_fraction=0.7):
    if not isinstance(closes, (list, tuple)) or len(closes) < 240:
        raise ValueError("At least 240 closes required")
    if any(type(x) not in (int, float) or not isfinite(x) or x <= 0 for x in closes):
        raise ValueError("Invalid price history")
    if not 0.6 <= train_fraction <= 0.8:
        raise ValueError("Train fraction outside permitted bounds")
    # Last available close is excluded from labelled examples; no future label.
    rows = [(_features(closes, t), int(closes[t+1] > closes[t]),
             closes[t+1] / closes[t] - 1) for t in range(LOOKBACK, len(closes)-1)]
    split = int(len(rows) * train_fraction)
    if split < 100 or len(rows)-split < 40:
        raise ValueError("Insufficient chronological train/holdout samples")
    weights = _fit([(f, y) for f, y, _ in rows[:split]])
    holdout = rows[split:]
    predictions = [_sigmoid(weights[0] + sum(w*x for w, x in zip(weights[1:], f)))
                   for f, _, _ in holdout]
    # Conservative, fixed threshold: only hold 5% notional when p >= 0.55.
    # Signal computed on close t; next close return t->t+1 is hypothetical,
    # not a realistically executable fill at close t. Do not treat as trade P&L.
    signals = [int(p >= 0.55) for p in predictions]
    correct = sum((p >= 0.5) == bool(y) for p, (_, y, _) in zip(predictions, holdout))
    majority = max(sum(y for _, y, _ in holdout),
                   sum(1-y for _, y, _ in holdout)) / len(holdout)
    brier = mean((p-y)**2 for p, (_, y, _) in zip(predictions, holdout))
    # Fees on signal transitions; no execution claim.
    previous = 0
    model_return = 0.0
    passive_return = 0.0
    for signal, (_, _, ret) in zip(signals, holdout):
        model_return += EXPOSURE * (signal * ret - abs(signal-previous)*COST_PER_SIDE)
        passive_return += EXPOSURE * ret
        previous = signal
    model_return -= EXPOSURE * previous * COST_PER_SIDE
    latest = _sigmoid(weights[0] + sum(w*x for w, x in zip(weights[1:], _features(closes, len(closes)-1))))
    return {**SAFE, "version": VERSION, "status": "EXPLORATORY_HOLDOUT_ONLY",
            "training_samples": split, "holdout_samples": len(holdout),
            "holdout_accuracy": round(correct/len(holdout), 6),
            "majority_class_baseline_accuracy": round(majority, 6),
            "holdout_brier_score": round(brier, 6),
            "hypothetical_model_simple_return_fraction": round(model_return, 6),
            "hypothetical_capped_hold_simple_return_fraction": round(passive_return, 6),
            "latest_model_up_probability_uncalibrated": round(latest, 6),
            "holdout_positive_signals": sum(signals),
            "limitations": ("Unadjusted daily close prices; one fixed chronological split; "
                            "non-executable same-close assumption, illustrative fees, no "
                            "dividends/FX/spread/fills, no tuning on holdout, correlated "
                            "assets, no proven edge. Probability not calibrated.")}


def run_local_ml_research(fetcher=fetch_daily_closes, tickers=WATCHLIST):
    results = {}
    for ticker in tickers:
        try:
            h = fetcher(ticker, period="5y")
            if h.get("ticker") != ticker:
                raise ValueError("Mismatched ticker")
            results[ticker] = evaluate_local_model(h["closes"])
        except (ValueError, TypeError, KeyError, OSError, IndexError, OverflowError) as exc:
            results[ticker] = {**SAFE, "status": "UNAVAILABLE",
                               "error_type": type(exc).__name__}
    return {**SAFE, "version": VERSION, "mode": "LOCAL_ML_OFFLINE_RESEARCH",
            "assets": results, "external_ai_api_calls": 0}


if __name__ == "__main__":
    print(json.dumps(run_local_ml_research(), indent=2))
