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
        # Treat empty string as missing so defaults can apply
        if val == "" and default is not None:
            val = default
    return val

ALPACA_API_KEY = get_env_var("ALPACA_API_KEY")
ALPACA_SECRET_KEY = get_env_var("ALPACA_SECRET_KEY")
GOOGLE_SERVICE_ACCOUNT_JSON = get_env_var("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_SHEET_ID = get_env_var("GOOGLE_SHEET_ID")

_paper_mode_raw = str(get_env_var("PAPER_MODE", "true", required=False)).lower()
PAPER_MODE = _paper_mode_raw not in ("false", "0", "f", "no")

_DEFAULT_WATCHLIST = "AAPL,MSFT,SPY,QQQ,NVDA,BTC/USD,ETH/USD"
_watchlist_raw = get_env_var("WATCHLIST", _DEFAULT_WATCHLIST, required=False)
if not _watchlist_raw:
    _watchlist_raw = _DEFAULT_WATCHLIST
WATCHLIST = [s.strip() for s in str(_watchlist_raw).split(",") if s.strip()]
if not WATCHLIST:
    WATCHLIST = [s.strip() for s in _DEFAULT_WATCHLIST.split(",") if s.strip()]

_DEFAULT_MR = "SPY,QQQ,AAPL"
_mr_raw = get_env_var("MEAN_REVERSION_ELIGIBLE", _DEFAULT_MR, required=False)
if not _mr_raw:
    _mr_raw = _DEFAULT_MR
MEAN_REVERSION_ELIGIBLE = [s.strip() for s in str(_mr_raw).split(",") if s.strip()]

POLL_INTERVAL_SECONDS = int(get_env_var("POLL_INTERVAL_SECONDS", "90", required=False))
LOOP_MAX_MINUTES = int(get_env_var("LOOP_MAX_MINUTES", "350", required=False))

RISK_PER_TRADE_PCT = float(get_env_var("RISK_PER_TRADE_PCT", "0.008", required=False))
MAX_TOTAL_RISK_PCT = float(get_env_var("MAX_TOTAL_RISK_PCT", "0.05", required=False))
MAX_DRAWDOWN_PCT = float(get_env_var("MAX_DRAWDOWN_PCT", "0.08", required=False))

GEMINI_API_KEY = get_env_var("GEMINI_API_KEY", required=False)
GEMINI_MODEL = get_env_var("GEMINI_MODEL", default="gemini-2.0-flash", required=False)

MIN_SIGNAL_CONFIDENCE = float(get_env_var("MIN_SIGNAL_CONFIDENCE", "0.55", required=False))
MAX_POSITION_PCT = float(get_env_var("MAX_POSITION_PCT", "0.18", required=False))
MAX_PORTFOLIO_EXPOSURE = float(get_env_var("MAX_PORTFOLIO_EXPOSURE", "0.75", required=False))
MAX_POSITIONS = int(get_env_var("MAX_POSITIONS", "8", required=False))
COOLDOWN_MINUTES = int(get_env_var("COOLDOWN_MINUTES", "720", required=False))
