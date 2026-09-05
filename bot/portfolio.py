import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PortfolioEngine:
    def __init__(self, max_portfolio_exposure: float, max_positions: int):
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_positions = max_positions

    def evaluate(self, symbol: str, signal: str, open_positions: List[Dict[str, Any]], current_price: float, equity: float) -> Dict[str, Any]:
        """
        Evaluate if taking this position violates portfolio-level constraints.
        """
        if signal == "HOLD":
            return {"approved": False, "reason": "Signal is HOLD"}

        if signal == "SELL":
            # We don't restrict sells/closes (unless it's shorting, which we avoid right now)
            return {"approved": True, "reason": "Sell orders approved by portfolio"}

        if signal == "BUY":
            num_open = len(open_positions)

            # Check if symbol already held
            sym_clean = symbol.upper().replace("-", "/").replace("/", "")
            already_held = False
            for p in open_positions:
                 held_sym = p["symbol"].upper().replace("-", "/").replace("/", "")
                 if held_sym == sym_clean:
                      already_held = True
                      break

            if already_held:
                 return {"approved": False, "reason": f"Already holding {symbol} (no averaging up/down allowed)"}

            if num_open >= self.max_positions:
                return {"approved": False, "reason": f"Max positions reached ({self.max_positions})"}

            # Calculate total exposure
            total_exposure = sum((abs(float(p["qty"])) * float(p["current_price"])) for p in open_positions)
            # Assuming a standard allocation size based on max positions.
            # Example: 90% max exposure / 10 max positions = 9% per position
            expected_allocation = equity * (self.max_portfolio_exposure / self.max_positions)

            new_exposure = total_exposure + expected_allocation
            max_allowed_exposure = equity * self.max_portfolio_exposure

            if new_exposure > max_allowed_exposure:
                return {"approved": False, "reason": f"Portfolio exposure limit reached (Expected: ${new_exposure:.2f} > Max: ${max_allowed_exposure:.2f})"}

            return {"approved": True, "reason": "Portfolio constraints passed"}
