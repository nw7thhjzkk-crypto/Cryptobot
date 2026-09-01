# Multi-Agent Paper Trading Bot

Professional multi-agent paper trading system built on **Alpaca** + **Google Sheets**.

Designed for reliability, clear regime detection, and clean risk management.
Optimized for paper trading (especially useful for users in India).

## Key Features (Upgraded)

- **Strong Market Regime Detection**  
  ADX + ATR + SMA 50/200 → `trending_bull`, `trending_bear`, `ranging`, `risk_off`, `transitional`

- **Improved Agents**
  - TrendAgent → ADX filter + volume confirmation
  - MeanReversionAgent → only trades in true ranging markets
  - Momentum, Breakout, Volume, Relative Strength, Volatility agents
  - Optional Gemini Context Agent (you have Gemini Pro)

- **Regime-aware Consensus**  
  Weights change automatically depending on market regime.

- **Solid Risk Management**  
  ATR-based position sizing, portfolio risk limits, drawdown breaker, max positions.

- **Clean Dashboard** (pure client-side)  
  Works with Netlify / any static host. Just paste your Google Sheet ID.

## Quick Start

1. Clone & install
```bash
pip install -r requirements.txt
```

2. Set secrets (GitHub Actions → Settings → Secrets)

Required:
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `GOOGLE_SERVICE_ACCOUNT_JSON` (full JSON as one line)
- `GOOGLE_SHEET_ID`
- `PAPER_MODE` = `true` (keep this true for now)

Optional:
- `WATCHLIST` (default already includes AAPL, MSFT, SPY, QQQ, NVDA, BTC/USD, ETH/USD)
- `MEAN_REVERSION_ELIGIBLE`
- `GEMINI_API_KEY` (recommended – you have Gemini Pro)

3. Share your Google Sheet  
   → **Anyone with the link can view** (required for the dashboard)

4. Run via GitHub Actions  
   Actions → Trading Bot → Run workflow

## Dashboard (Recommended: Netlify)

The dashboard is now **pure client-side**. No backend needed.

### Deploy to Netlify (free & best)

1. Go to [netlify.com](https://netlify.com) and connect this GitHub repo
2. Set publish directory to `dashboard`
3. Deploy
4. Open the site → paste your Google Sheet ID → Load

You can also just open `dashboard/index.html` locally.

## Important Notes for India

- Keep **PAPER_MODE=true**. Alpaca paper trading works fully for Indian residents.
- Live trading for individual Indian accounts still has restrictions (Alpaca is expanding via GIFT City).
- Crypto pairs (`BTC/USD`, `ETH/USD`) work in paper mode.
- This setup is excellent for strategy development and learning.

## Architecture

```
bot/
├── agents/          # Individual specialized agents
├── consensus.py     # Regime-aware voting + Gemini veto
├── risk.py          # Position sizing + risk checks
├── execution.py     # Order submission with retries
├── broker.py        # Alpaca client
├── sheets.py        # Google Sheets logging
└── main.py          # Main loop
```

## Next Improvements (optional)

- Trailing stops
- More Freqtrade-inspired strategies
- Simple backtester
- Telegram notifications

---

**Stay in paper mode until the strategies prove themselves over weeks of data.**
