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

_paper_mode_raw = str(get_env_var("PAPER_MODE", "true", required=False)).lower()
PAPER_MODE = _paper_mode_raw not in ("false", "0", "f", "no")

# Default watchlist: liquid US stocks + major crypto pairs supported by Alpaca paper
WATCHLIST = [s.strip() for s in get_env_var(
    "WATCHLIST",
    "AAPL,MSFT,SPY,QQQ,NVDA,BTC/USD,ETH/USD"
).split(",") if s.strip()]

MEAN_REVERSION_ELIGIBLE = [s.strip() for s in get_env_var(
    "MEAN_REVERSION_ELIGIBLE",
    "SPY,QQQ,AAPL"
).split(",") if s.strip()]

POLL_INTERVAL_SECONDS = int(get_env_var("POLL_INTERVAL_SECONDS", "90"))
LOOP_MAX_MINUTES = int(get_env_var("LOOP_MAX_MINUTES", "350"))

# Risk - slightly more conservative
RISK_PER_TRADE_PCT = float(get_env_var("RISK_PER_TRADE_PCT", "0.008"))
MAX_TOTAL_RISK_PCT = float(get_env_var("MAX_TOTAL_RISK_PCT", "0.05"))
MAX_DRAWDOWN_PCT = float(get_env_var("MAX_DRAWDOWN_PCT", "0.08"))

GEMINI_API_KEY = get_env_var("GEMINI_API_KEY", required=False)
GEMINI_MODEL = get_env_var("GEMINI_MODEL", default="gemini-2.0-flash", required=False)

MIN_SIGNAL_CONFIDENCE = float(get_env_var("MIN_SIGNAL_CONFIDENCE", "0.55"))
MAX_POSITION_PCT = float(get_env_var("MAX_POSITION_PCT", "0.18"))
MAX_PORTFOLIO_EXPOSURE = float(get_env_var("MAX_PORTFOLIO_EXPOSURE", "0.75"))
MAX_POSITIONS = int(get_env_var("MAX_POSITIONS", "8"))
COOLDOWN_MINUTES = int(get_env_var("COOLDOWN_MINUTES", "720"))  # 12 hours
