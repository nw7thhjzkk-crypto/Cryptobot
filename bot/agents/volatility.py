import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.factors import calculate_volatility

class VolatilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("VolatilityAgent", version="1.1", parameters={"vol_length": 20}, regime_compatibility=["high_volatility", "trending_bull", "trending_bear"])

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < self.parameters["vol_length"] + 5:
            return self._create_hold_signal(symbol, "Insufficient data for Volatility Agent")

        df = price_history.copy()

        vol = calculate_volatility(df, length=self.parameters["vol_length"])

        if vol is None or vol.empty:
             return self._create_hold_signal(symbol, "Failed to calc volatility")

        curr_vol = float(vol.iloc[-1])
        avg_vol = float(vol.iloc[-self.parameters["vol_length"]:-1].mean())

        signal = "HOLD"
        confidence = 0.0
        reason = "Normal volatility"

        vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1.0

        if vol_ratio > 1.5:
             # Just an example implementation - can be extended
             signal = "HOLD"
             confidence = 0.5
             reason = f"High volatility regime (Ratio: {vol_ratio:.2f})"

        return {
            "agent": self.name,
            "version": self.version,
            "symbol": symbol,
            "signal": signal,
            "score": 0.0,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "realized_vol": curr_vol,
                "vol_ratio": vol_ratio
            }
        }
