import pandas as pd
from typing import Dict, Any

class BaseAgent:
    def __init__(self, name: str, version: str = "1.0", parameters: dict = None, regime_compatibility: list = None):
        self.name = name
        self.version = version
        self.parameters = parameters or {}
        # By default, compatible with all if None
        self.regime_compatibility = regime_compatibility
        self.expected_holding_period = None
        self.transaction_cost_sensitivity = None

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement analyze method.")

    def _create_hold_signal(self, symbol: str, reason: str, features: dict = None) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "version": self.version,
            "symbol": symbol,
            "signal": "HOLD",
            "score": 0.0,
            "confidence": 0.0,
            "reason": reason,
            "features": features or {}
        }
