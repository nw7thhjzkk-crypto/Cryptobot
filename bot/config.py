import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_env_var(name, default=None, required=True):
    val = os.getenv(name, default)
    if required and val is None:
        print(f"CRITICAL ERROR: Missing required environment variable {name}", file=sys.stderr)
        sys.exit(1)
    if isinstance(val, str):
        val = val.strip()
    return val

ALPACA_API_KEY = get_env_var("ALPACA_API_KEY")
ALPACA_SECRET_KEY = get_env_var("ALPACA_SECRET_KEY")
GOOGLE_SERVICE_ACCOUNT_JSON = get_env_var("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_SHEET_ID = get_env_var("GOOGLE_SHEET_ID")
PAPER_MODE = get_env_var("PAPER_MODE", "true").lower() == "true"
WATCHLIST = get_env_var("WATCHLIST", "AAPL,MSFT,SPY").split(",")
MEAN_REVERSION_ELIGIBLE = get_env_var("MEAN_REVERSION_ELIGIBLE", "SPY").split(",")
POLL_INTERVAL_SECONDS = int(get_env_var("POLL_INTERVAL_SECONDS", "60"))
LOOP_MAX_MINUTES = int(get_env_var("LOOP_MAX_MINUTES", "350"))
RISK_PER_TRADE_PCT = float(get_env_var("RISK_PER_TRADE_PCT", "0.01"))
MAX_TOTAL_RISK_PCT = float(get_env_var("MAX_TOTAL_RISK_PCT", "0.06"))
MAX_DRAWDOWN_PCT = float(get_env_var("MAX_DRAWDOWN_PCT", "0.10"))
