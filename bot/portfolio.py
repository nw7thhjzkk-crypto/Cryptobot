import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PortfolioEngine:
    def __init__(self, max_portfolio_exposure: float, max_positions: int, max_symbol_exposure: float = 0.2, allocation_method: str = "equal"):
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_positions = max_positions
        self.max_symbol_exposure = max_symbol_exposure
        self.allocation_method = allocation_method

    def calculate_allocation(self, symbol: str, equity: float, volatility: float = None) -> float:
        """Calculate target cash allocation based on method."""
        base_allocation = equity * (self.max_portfolio_exposure / self.max_positions)

        if self.allocation_method == "inverse_volatility" and volatility and volatility > 0:
            adj = min(max(0.5 / volatility, 0.5), 1.5)
            target = base_allocation * adj
        else:
            target = base_allocation

        return min(target, equity * self.max_symbol_exposure)

    def evaluate(self, symbol: str, signal: str, open_positions: List[Dict[str, Any]], current_price: float, equity: float, symbol_volatility: float = None) -> Dict[str, Any]:
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
            expected_allocation = self.calculate_allocation(symbol, equity, symbol_volatility)

            if expected_allocation > (equity * self.max_symbol_exposure):
                 return {"approved": False, "reason": f"Symbol allocation limit reached (${expected_allocation:.2f} > max ${equity * self.max_symbol_exposure:.2f})"}

            new_exposure = total_exposure + expected_allocation
            max_allowed_exposure = equity * self.max_portfolio_exposure

            if new_exposure > max_allowed_exposure:
                return {"approved": False, "reason": f"Portfolio exposure limit reached (Expected: ${new_exposure:.2f} > Max: ${max_allowed_exposure:.2f})"}

            return {"approved": True, "reason": "Portfolio constraints passed", "target_allocation": expected_allocation}
