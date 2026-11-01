# Project E.T. demo research review bridge

This stage joins **offline research decisions** to **eToro DEMO read-only data snapshots**. It does NOT link your ChatGPT OAuth connection to GitHub Actions. GitHub cannot automatically reuse the ChatGPT eToro connection or its authorization token.

## Current data inputs

The offline function `build_demo_review` in `demo_decision_bridge.py` accepts four dictionaries:

1. `run_central_research_cycle.run_research_cycle()` result (requires complete, aligned historical research).
2. An unfiltered eToro DEMO `get_my_portfolio_summary(account="demo")` result.
3. An unfiltered eToro DEMO `get_my_positions_and_orders(account="demo")` result (including timestamp, direct positions/orders and mirrors).
4. A recent eToro `get_instruments_overview(symbols=[...])` result for the candidate instruments.

It additionally requires the current UTC time, an **independently verified market-open state** and **historical peak demo equity** tracked across sessions. A single portfolio snapshot cannot establish the historical peak: resetting the peak after a loss would disable the drawdown safeguard.

A local example using JSON files provided to your own machine:

```shell
python tools/run_demo_review.py central_research_cycle.json demo_portfolio.json demo_positions.json market_overview.json --peak-equity-usd 100000
```

By default the CLI intentionally treats the market as **not verified open**. The `--market-open-verified` switch must only be used when reliable session/holiday data confirms the market is trading; quote freshness alone does not establish that fact.

**Do not commit brokerage snapshots, account IDs, OAuth tokens, or API keys into this public repository.** The example snapshot names are local working files, not tracked artifacts.

## Safety and limitations

- Read-only and offline: no connector call, network access, order execution, position edits or account changes.
- Rejects non-demo, unverified and stale data; pending orders or copied positions, filtered portfolio reads, missing peak equity, mismatched research allocations, stale quotes, closed/unknown market, leveraged or oversized proposals.
- Uses a separate **$1,000 virtual training budget** for sizing. At most $25 is proposed per candidate, with a $50 per-position cap and $100 total exposure cap in the risk gate. This is not a recommended real-money trading size.
- Only `ELIGIBLE_FOR_SIMULATION` research labels can become human-review candidates; the six heuristic perspectives are not predictive AI models and should not be assumed to have an edge.
- The broad market overview eligibility is provisional. Before any eToro demo order, verify the precise demo account's live price, settlement, fees, spread, minimum size, leverage and eligibility using eToro's official order preparation.
- **Every order requires an explicit user confirmation on its exact terms**; eToro must still approve it. A `READY_FOR_USER_REVIEW` label does not place or authorize a trade.
- The review is point-in-time. Recheck all snapshots immediately before preparing any approved demo order. No daemon or 24/7 autonomous trader is running.

## Validation

```shell
python -m unittest discover -s tests -v
```

Tests include no-execution guarantee, broker read failures, demo-only mode, stale weekend quotes, pending orders, missing historical peak, drawdown and exposure limits.
