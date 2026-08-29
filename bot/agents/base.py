import pandas as pd
from typing import Dict, Any

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement analyze method.")

    def _create_hold_signal(self, symbol: str, reason: str, features: dict = None) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": "HOLD",
            "score": 0.0,
            "confidence": 0.0,
            "reason": reason,
            "features": features or {}
        }
