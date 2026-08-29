import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class PortfolioEngine:
    def __init__(self, max_portfolio_exposure: float, max_positions: int):
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_positions = max_positions

    def evaluate(self, symbol: str, signal: str, open_positions: List[Dict[str, Any]], current_price: float, equity: float) -> Dict[str, Any]:
        if signal == "HOLD":
            return {"approved": False, "reason": "Signal is HOLD"}

        existing_pos = next((p for p in open_positions if p['symbol'] == symbol), None)

        if signal == "SELL":
            if not existing_pos:
                return {"approved": False, "reason": f"No existing position to sell for {symbol}"}
            if existing_pos['qty'] <= 0:
                return {"approved": False, "reason": f"Existing position qty is {existing_pos['qty']} for {symbol}"}
            return {"approved": True, "reason": "Sell approved for existing position"}

        if signal == "BUY":
            if existing_pos and existing_pos['qty'] > 0:
                return {"approved": False, "reason": f"Already hold position in {symbol}"}

            if len(open_positions) >= self.max_positions:
                return {"approved": False, "reason": f"Max positions ({self.max_positions}) reached"}

            current_exposure = 0.0
            for p in open_positions:
                current_exposure += (p['qty'] * p['current_price'])

            if equity > 0:
                exposure_pct = current_exposure / equity
                if exposure_pct >= self.max_portfolio_exposure:
                    return {"approved": False, "reason": f"Portfolio exposure ({exposure_pct:.2f}) exceeds max allowed ({self.max_portfolio_exposure})"}
            else:
                 return {"approved": False, "reason": "Invalid equity (<=0)"}

            return {"approved": True, "reason": "Buy approved by portfolio constraints"}

        return {"approved": False, "reason": f"Unknown signal {signal}"}
