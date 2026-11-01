# Project E.T. — eToro API connection diagnosis (demo only)

## What is confirmed

- The ChatGPT-connected eToro OAuth integration successfully submitted and filled a $100 ETHEUR **demo** order on 2026-11-01.
- The separate GitHub Actions API-key connection previously received HTTP 403. OAuth success does **not** authenticate GitHub Actions.
- Existing `tools/check_etoro_account_read_access.py` makes GET requests only, using `ETORO_PUBLIC_KEY` and `ETORO_USER_KEY` GitHub secrets.

## Safe troubleshooting sequence

1. In the eToro developer portal, confirm the key pair is **active**, belongs to the intended account and has **demo portfolio read** access. Check whether the public/API key and user key are different values. Do not paste either into issues, PRs, chats or logs.
2. In GitHub repository **Settings → Secrets and variables → Actions**, verify the secret names are exactly `ETORO_PUBLIC_KEY` and `ETORO_USER_KEY`. Repository secrets are not inherited from the ChatGPT eToro connector. If rotated, update both together.
3. Manually run **eToro read-only connection diagnostics** from the Actions tab. Inspect only status codes for identity, real and demo. No response bodies, tokens or balances should be logged.
4. HTTP 401 generally means authentication failed; HTTP 403 means access was denied but **does not by itself prove** whether the cause is permissions, key/account/environment mismatch, account restrictions or an API entitlement. Confirm the exact route and required headers against eToro's current official developer documentation. If 403 persists with a newly verified key, contact eToro developer support with request IDs and redacted route/status details.
5. Do not add demo-write secrets or schedule execution until demo READ returns 200, API response schemas are validated and end-to-end order/position reconciliation tests pass. A separate explicit approval and kill switch are required before any unattended demo execution.

## Profit protection

`etoro_demo_profit_guard.py` produces offline proposals for 5% take-profit and 5% stop-loss based on verified unrealised P/L. It **does not** edit eToro positions. Broker-side take-profit and stop-loss values may be price levels rather than percentages and must be computed from eToro's current position and checked against broker constraints. Periodic GitHub Actions runs are not reliable for fast market exits; if protection is desired, use separately approved broker-native risk orders.

**Current state: READ-ONLY DIAGNOSTICS / NO AUTONOMOUS EXECUTION.**
