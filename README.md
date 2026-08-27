# Paper Trading Bot

This repository contains a Python-based paper trading bot that connects to the Alpaca API for executing trades and Google Sheets for logging activity. The bot uses regime detection (trending vs ranging) to choose between different trading strategies and includes comprehensive risk management.

## Setup Instructions

1.  **Clone the repository** and install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**: Create a `.env` file (or set these in your environment) based on `.env.example`.

### Obtaining Credentials

*   **Alpaca API Keys**: Go to the Alpaca dashboard, switch to Paper Trading, and generate a new set of API keys.
*   **Google Service Account JSON**: Go to the Google Cloud Console, create a project, enable the Google Sheets API and Google Drive API. Create a Service Account, generate a JSON key, and download it. Minimize the JSON to a single line to use as the `GOOGLE_SERVICE_ACCOUNT_JSON` secret.
*   **Google Sheet ID**: Create a new Google Sheet. Share it with the email address of the Google Service Account you created (giving it Editor access). The Sheet ID is the long alphanumeric string in the URL between `/d/` and `/edit`.
*   **Important for Dashboard**: To allow the client-side dashboard to read the Sheet without a backend, click "Share" in the top right of your Google Sheet, and change General Access to **"Anyone with the link can view"**.

### GitHub Repo Secrets (Settings -> Secrets and variables -> Actions)

Add the following secrets to match `bot/config.py`:
*   `ALPACA_API_KEY`
*   `ALPACA_SECRET_KEY`
*   `GOOGLE_SERVICE_ACCOUNT_JSON`
*   `GOOGLE_SHEET_ID`
*   `PAPER_MODE` (default "true")
*   `WATCHLIST`
*   `MEAN_REVERSION_ELIGIBLE`

## Using the Dashboard

The dashboard now runs entirely in the browser using the standalone `dashboard/index.html` file (no backend or Netlify required).
1. Open `dashboard/index.html` in your browser (or host it statically).
2. Enter your Google Sheet ID in the input box at the top right.
3. Click "Load Data". (Ensure you completed the step above to make the sheet viewable).

## Testing the Bot Manually

You can manually trigger the bot using GitHub Actions:
1. Go to the **Actions** tab in your GitHub repository.
2. Select the **Trading Bot** workflow on the left.
3. Click the **Run workflow** button on the right side and select the branch.

## Phase 2 / Later

Once you have conducted extensive paper testing across walk-forward validation, you can switch the bot to live trading. **Do not do this casually.**

To go live:
1.  Change `PAPER_MODE` to `false` in your environment variables/secrets.
2.  Update `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` with your Live Alpaca keys.