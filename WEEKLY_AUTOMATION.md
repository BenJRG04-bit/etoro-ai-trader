# Automated weekly offline research

The `weekly-offline-research.yml` GitHub Actions workflow is scheduled for Mondays at **07:15 UTC**. It can also be launched manually from the Actions tab.

It runs all offline unit tests first, then produces six separate public-market-data reports (paper comparison, decision diagnostics, veto outcomes, multi-horizon severity, chronological audit and sample quality), plus a machine-readable summary. Download the **project-et-weekly-offline-research** artifact from a completed run. Artifacts are retained for 30 days.

**Safety:** It uses public historical prices, no eToro keys, no broker access, no trade placement, no auto-merge and no live trading. Repository workflow permissions are read-only.

**Limitations:** GitHub scheduled runs can be delayed or skipped during platform disruption, and GitHub may disable schedules for inactive repositories. Public data may be temporarily unavailable. The summary marks unavailable assets rather than inventing results. A successful workflow only means software checks and data retrieval completed; it is **not** proof that the strategy is profitable, ready for real-money trading, or reliably autonomous. The same history may be re-evaluated each week, so it is not independent validation.

**Review:** Check GitHub Actions periodically for failures and examine the saved reports. No automatic chat notification or unattended code changes are configured.
