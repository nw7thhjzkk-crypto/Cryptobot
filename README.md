# Multi-Agent Paper Trading Bot

A production-ready multi-agent paper trading system for **Alpaca** with persistent state in **Google Sheets** and a clean client-side dashboard.

Designed to run continuously on free GitHub Actions (handles the 6-hour limit by chaining runs and loading previous equity history).

---

## Features

### Strategy Engine
- **Market Regime Detection** — ADX + ATR + SMA structure → `trending_bull`, `trending_bear`, `ranging`, `risk_off`, `transitional`
- **Specialized Agents**
  - Trend (ADX + volume filtered)
  - Mean Reversion (only in ranging markets)
  - Momentum, Breakout, Volume, Volatility, Relative Strength
  - Gemini Context Agent (adversarial risk check – works with your Gemini Pro key)
- **Regime-aware Consensus** — agent weights automatically adjust by market regime
- **Risk Management** — ATR position sizing, portfolio risk limits, drawdown breaker, max positions

### Infrastructure
- Continuous paper trading across GitHub Actions runs
- Equity history + positions persisted in Google Sheets
- Pure client-side dashboard (no backend required)
- Netlify-ready static frontend

---

## Setup (5 minutes)

### 1. Secrets (GitHub → Settings → Secrets and variables → Actions)

| Secret | Required | Notes |
|--------|----------|-------|
| `ALPACA_API_KEY` | Yes | Paper keys |
| `ALPACA_SECRET_KEY` | Yes | Paper keys |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Full JSON as one line |
| `GOOGLE_SHEET_ID` | Yes | From the sheet URL |
| `PAPER_MODE` | Yes | Set to `true` |
| `GEMINI_API_KEY` | Recommended | You have Gemini Pro |
| `WATCHLIST` | Optional | Default includes stocks + BTC/USD + ETH/USD |

### 2. Google Sheet
Share the sheet as **Anyone with the link can view** (required for the dashboard).

### 3. Run the bot
Actions → **Trading Bot** → **Run workflow**

The bot will also run automatically every ~6 hours.

---

## Dashboard

### Best option: Netlify (free)
1. Connect this repository to Netlify
2. Set publish directory to `dashboard`
3. Deploy
4. Open the site → paste your Google Sheet ID → Load

### Alternative
Just open `dashboard/index.html` in a browser and paste the Sheet ID.

---

## Important Notes for India Users

- Keep **`PAPER_MODE=true`**. This is the correct and safe setting.
- Alpaca paper trading works fully for Indian residents.
- Live trading for individual Indian accounts still has restrictions.
- Crypto pairs (`BTC/USD`, `ETH/USD`) work in paper mode.

---

## How Continuous Running Works

1. Bot runs for ~5.5–5.8 hours (safe under GitHub’s 6-hour limit)
2. Saves final equity + positions to Google Sheets
3. Exits cleanly
4. Next scheduled run starts, loads previous equity history, and continues with the same open positions from Alpaca

This gives you effectively continuous paper trading for free.

---

## Architecture

```
bot/
├── agents/               # Specialized trading agents
├── consensus.py          # Regime-aware voting + Gemini veto
├── risk.py               # Position sizing + risk checks + trailing helpers
├── execution.py          # Order submission with retries
├── broker.py             # Alpaca client
├── sheets.py             # Google Sheets (state + logging)
└── main.py               # Main continuous loop

dashboard/
└── index.html            # Pure client-side dashboard
```

---

## Recommended Usage

1. Run in paper mode for several weeks
2. Watch the dashboard and the Trades / Equity tabs
3. Only consider live trading after you have clear positive edge and understand the risks

**This is a paper-trading system. Trading involves risk of loss.**
