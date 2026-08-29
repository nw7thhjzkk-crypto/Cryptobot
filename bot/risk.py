import math
import pandas as pd

def calculate_position_size(account_equity: float, atr: float, risk_per_trade_pct: float, stop_multiple: float = 2.0) -> int:
    """
    Returns (risk_per_trade_pct * account_equity) / (atr * stop_multiple),
    rounded down to a whole share count.
    """
    if atr <= 0: return 0
    risk_amount = account_equity * risk_per_trade_pct
    risk_per_share = atr * stop_multiple
    shares = math.floor(risk_amount / risk_per_share)
    return shares

def calculate_stop_price(entry_price: float, atr: float, side: str, stop_multiple: float = 2.0) -> float:
    """
    Returns the stop-loss price, stop_multiple * atr away from entry
    in the adverse direction.
    """
    if side.lower() == 'buy':
        return entry_price - (stop_multiple * atr)
    else:
        return entry_price + (stop_multiple * atr)

def check_portfolio_risk(open_positions: list, new_position_risk: float, max_total_risk_pct: float, account_equity: float) -> bool:
    """
    Sums risk already committed across open_positions plus the new
    position's risk, returns False if this would exceed
    max_total_risk_pct of equity.
    (Assuming open_positions risk is unrealized loss if any, or a predefined risk per position).
    For simplicity, we estimate committed risk as max(0, avg_entry - current) * qty for longs.
    A more rigorous approach would store the initial risk or stop loss.
    Here we simply approximate.
    """
    total_open_risk = 0.0
    for pos in open_positions:
        # crude approximation of risk on current position if stop was not tracked
        # ideally we should track the initial stop.
        # we will use unrealized_pl if negative as current risk, but it's a proxy.
        if pos['unrealized_pl'] < 0:
            total_open_risk += abs(pos['unrealized_pl'])

    total_projected_risk = total_open_risk + new_position_risk
    max_allowed_risk = account_equity * max_total_risk_pct

    return total_projected_risk <= max_allowed_risk

def check_drawdown_breaker(equity_history: list, max_drawdown_pct: float, window_days: int = 30) -> bool:
    """
    Returns True (halt new entries) if equity has drawn down more than
    max_drawdown_pct from its peak within the trailing window_days.
    """
    if not equity_history:
        return False

    # take last window_days of equity
    recent_equity = equity_history[-window_days:]
    if not recent_equity:
        return False

    peak = max(recent_equity)
    current = recent_equity[-1]

    drawdown = (peak - current) / peak if peak > 0 else 0
    return drawdown > max_drawdown_pct

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self, paper_mode: bool, max_position_pct: float):
        self.paper_mode = paper_mode
        self.max_position_pct = max_position_pct

    def evaluate_order(self, symbol: str, signal: str, qty: int, price: float, equity: float, buying_power: float) -> Dict[str, Any]:
        if signal == "HOLD":
             return {"approved": False, "reason": "Signal is HOLD"}

        if qty <= 0:
             return {"approved": False, "reason": "Quantity is zero or negative"}

        if equity <= 0:
             return {"approved": False, "reason": "Account equity is zero or negative"}

        if price <= 0 or math.isnan(price) or math.isinf(price):
             return {"approved": False, "reason": "Invalid price data"}

        if not self.paper_mode:
            logger.warning("LIVE TRADING MODE DETECTED. Proceeding with extreme caution.")

        position_value = qty * price

        max_allowed_value = equity * self.max_position_pct
        if position_value > max_allowed_value:
             return {"approved": False, "reason": f"Position value ({position_value}) exceeds max allowed ({max_allowed_value})"}

        if signal == "BUY" and position_value > buying_power:
             return {"approved": False, "reason": f"Insufficient buying power (Needs {position_value}, has {buying_power})"}

        return {"approved": True, "reason": "Risk checks passed"}
