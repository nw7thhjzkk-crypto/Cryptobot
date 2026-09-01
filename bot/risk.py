import math
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def calculate_position_size(
    account_equity: float,
    atr: float,
    risk_per_trade_pct: float,
    stop_multiple: float = 2.0,
    max_shares: Optional[int] = None
) -> int:
    """
    Volatility-adjusted position sizing.
    Risk a fixed % of equity based on ATR distance to stop.
    """
    if atr <= 0 or account_equity <= 0:
        return 0

    risk_amount = account_equity * risk_per_trade_pct
    risk_per_share = atr * stop_multiple

    if risk_per_share <= 0:
        return 0

    shares = math.floor(risk_amount / risk_per_share)

    if max_shares is not None:
        shares = min(shares, max_shares)

    return max(shares, 0)


def calculate_stop_price(entry_price: float, atr: float, side: str, stop_multiple: float = 2.0) -> float:
    """Initial stop loss price."""
    if side.lower() in ("buy", "long"):
        return entry_price - (stop_multiple * atr)
    else:
        return entry_price + (stop_multiple * atr)


def calculate_trailing_stop(
    entry_price: float,
    current_price: float,
    atr: float,
    side: str,
    current_stop: Optional[float] = None,
    trail_multiple: float = 2.5
) -> float:
    """
    Simple ATR trailing stop.
    For longs: stop only moves up.
    For shorts: stop only moves down.
    """
    if side.lower() in ("buy", "long"):
        new_stop = current_price - (trail_multiple * atr)
        if current_stop is None:
            return new_stop
        return max(current_stop, new_stop)  # only ratchet up
    else:
        new_stop = current_price + (trail_multiple * atr)
        if current_stop is None:
            return new_stop
        return min(current_stop, new_stop)  # only ratchet down


def check_portfolio_risk(
    open_positions: list,
    new_position_risk: float,
    max_total_risk_pct: float,
    account_equity: float
) -> bool:
    """
    Approximate total risk.
    Uses unrealized loss as proxy for open risk + the new trade's planned risk.
    """
    total_open_risk = 0.0
    for pos in open_positions:
        # Prefer unrealized loss as current risk proxy
        if pos.get("unrealized_pl", 0) < 0:
            total_open_risk += abs(pos["unrealized_pl"])
        else:
            # Fallback: rough 2% of position value as risk
            pos_value = abs(pos.get("qty", 0) * pos.get("current_price", 0))
            total_open_risk += pos_value * 0.02

    total_projected = total_open_risk + new_position_risk
    max_allowed = account_equity * max_total_risk_pct

    return total_projected <= max_allowed


def check_drawdown_breaker(equity_history: list, max_drawdown_pct: float, window: int = 80) -> bool:
    """
    Halt new entries if we are down more than max_drawdown_pct from the recent peak.
    Works across multiple GitHub Actions runs because we load history from Sheets.
    """
    if not equity_history or len(equity_history) < 3:
        return False

    recent = equity_history[-window:]
    peak = max(recent)
    current = recent[-1]

    if peak <= 0:
        return False

    drawdown = (peak - current) / peak
    return drawdown > max_drawdown_pct


class RiskEngine:
    def __init__(self, paper_mode: bool, max_position_pct: float):
        self.paper_mode = paper_mode
        self.max_position_pct = max_position_pct

    def evaluate_order(
        self,
        symbol: str,
        signal: str,
        qty: int,
        price: float,
        equity: float,
        buying_power: float
    ) -> Dict[str, Any]:

        if signal == "HOLD":
            return {"approved": False, "reason": "Signal is HOLD"}

        if qty <= 0:
            return {"approved": False, "reason": "Quantity is zero or negative"}

        if equity <= 0:
            return {"approved": False, "reason": "Account equity is zero or negative"}

        if price <= 0 or math.isnan(price) or math.isinf(price):
            return {"approved": False, "reason": "Invalid price data"}

        if not self.paper_mode:
            logger.warning("LIVE TRADING MODE DETECTED. Extreme caution.")

        position_value = qty * price
        max_allowed_value = equity * self.max_position_pct

        if position_value > max_allowed_value:
            return {
                "approved": False,
                "reason": f"Position value ${position_value:.0f} exceeds max ${max_allowed_value:.0f}"
            }

        if signal == "BUY" and position_value > buying_power:
            return {
                "approved": False,
                "reason": f"Insufficient buying power (need ${position_value:.0f}, have ${buying_power:.0f})"
            }

        return {"approved": True, "reason": "Risk checks passed"}
