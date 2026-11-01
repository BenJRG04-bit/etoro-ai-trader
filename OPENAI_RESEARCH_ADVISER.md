# Project E.T. — Optional OpenAI research adviser

The AI adviser is not an autonomous trading agent. It interprets the five public daily-close pattern summaries using six named perspectives: trend, skeptic, historical, emerging, risk and benchmark. It never receives eToro keys, account balances, orders or personal portfolio data.

## Setup on GitHub

1. Visit your repository Settings → Secrets and variables → Actions → New repository secret.
2. Create a secret named exactly OPENAI_API_KEY. Paste the OpenAI developer platform secret key there only. Do not share it in chat, code, issues or logs.
3. The workflow Project ET optional OpenAI read-only research runs on weekdays and can be started manually using Actions → Run workflow.
4. Until the secret exists, it reports NOT_CONFIGURED and makes no API calls. This is intentional. The workflow also has a short timeout and a fixed max_output_tokens request cap. API calls can incur charges even if no trade is placed. Check your OpenAI API usage and billing limits separately.

## Outputs

- RESEARCH_ONLY: validated six-perspective opinions on all five tickers.
- NOT_CONFIGURED: no API secret, no network request.
- UNAVAILABLE: missing public data, model refusal/incomplete output, invalid structure, network/API errors or a model attempt to override hard vetoes.

None of these statuses authorizes an order. The model cannot change the fixed strategy, backtest results, forward evaluation records or risk gates.

## Important limitations

The model receives only technical price-pattern evidence; it does not have independent real-time news, fundamentals, earnings, spreads or broker quotes. It can be wrong, agree with flawed premises or hallucinate. AI opinions are not an independent profitability test. Archived forward outcomes remain the main evidence standard. No live trading is implemented or enabled.
