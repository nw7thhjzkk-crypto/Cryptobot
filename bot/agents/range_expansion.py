import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.factors import calculate_atr

class RangeExpansionAgent(BaseAgent):
    def __init__(self, atr_lookback: int = 14, multiple: float = 1.5, min_history: int = 30):
        super().__init__("RangeExpansionAgent", version="1.1", parameters={"atr_lookback": atr_lookback, "multiple": multiple}, regime_compatibility=["ranging", "transitional"])
        self.atr_lookback = atr_lookback
        self.multiple = multiple
        self.min_history = min_history

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < self.min_history:
            return self._create_hold_signal(symbol, "Insufficient data for range expansion analysis")

        df = price_history.copy()
        atr = calculate_atr(df, length=self.atr_lookback)

        if atr is None or atr.empty:
            return self._create_hold_signal(symbol, "Failed to calculate ATR")

        curr_atr = float(atr.iloc[-2]) # Use previous bar ATR to avoid using expanded bar in its own calculation
        curr_range = float(df['high'].iloc[-1] - df['low'].iloc[-1])
        curr_close = float(df['close'].iloc[-1])
        curr_open = float(df['open'].iloc[-1])

        signal = "HOLD"
        confidence = 0.0
        reason = "Normal range"

        # Determine if today's range is an expansion
        if curr_range > curr_atr * self.multiple:
            # Bullish expansion: large range, close near high, above open
            if curr_close > curr_open and (curr_close - df['low'].iloc[-1]) / curr_range > 0.7:
                signal = "BUY"
                confidence = min(0.6 + (curr_range / curr_atr - self.multiple) * 0.2, 0.95)
                reason = f"Bullish range expansion (Range={curr_range:.2f}, ATR={curr_atr:.2f})"
            # Bearish expansion: large range, close near low, below open
            elif curr_close < curr_open and (df['high'].iloc[-1] - curr_close) / curr_range > 0.7:
                signal = "SELL"
                confidence = min(0.6 + (curr_range / curr_atr - self.multiple) * 0.2, 0.95)
                reason = f"Bearish range expansion (Range={curr_range:.2f}, ATR={curr_atr:.2f})"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "version": self.version,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "curr_range": curr_range,
                "prev_atr": curr_atr,
                "range_multiple": curr_range / curr_atr if curr_atr > 0 else 0
            }
        }
