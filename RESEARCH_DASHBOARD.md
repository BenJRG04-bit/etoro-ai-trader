# Project E.T. unified offline dashboard

The weekly GitHub Actions research workflow generates `research_dashboard.html` from the six JSON research reports and includes it in the downloadable `project-et-weekly-offline-research` artifact.

To view: open GitHub Actions, choose a completed **Project ET weekly offline research** run, download the artifact, unzip it and open `research_dashboard.html` locally in a browser. The HTML contains no scripts, remote assets, broker connections, or trading controls.

Columns show per-asset report availability, historical sample-count checks, the strategy's hypothetical £100 ending equity, a matched 5%-capped buy-and-hold ending equity, worst observed 20-day return after a veto, and the number of later-period 20-day veto observations. Missing data is shown as N/A.

This is an **offline historical research dashboard**, not a live account dashboard. A passing test or adequate sample count does not establish profitable or safe trading. Historical windows overlap, prices are unadjusted, and there is no FX, dividend, spread, slippage or tax model. No live orders or automatic strategy changes are possible.
