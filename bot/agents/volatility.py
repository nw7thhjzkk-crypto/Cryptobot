import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_atr

class VolatilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("VolatilityAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 30:
            return self._create_hold_signal(symbol, "Insufficient data for volatility analysis")

        df = price_history.copy()
        atr = calculate_atr(df, length=14)

        if atr is None or atr.empty:
            return self._create_hold_signal(symbol, "Failed to calculate ATR")

        curr_atr = atr.iloc[-1]
        atr_avg = atr.rolling(window=20).mean().iloc[-1]

        ema10 = df['close'].ewm(span=10, adjust=False).mean()
        curr_close = df['close'].iloc[-1]

        signal = "HOLD"
        confidence = 0.0
        reason = "Normal volatility regime"

        if curr_atr > atr_avg * 1.5:
            if curr_close > ema10.iloc[-1]:
                 signal = "BUY"
                 confidence = min(0.5 + (curr_atr / atr_avg - 1.5) * 0.5, 0.9)
                 reason = "High volatility expansion in bullish direction"
            elif curr_close < ema10.iloc[-1]:
                 signal = "SELL"
                 confidence = min(0.5 + (curr_atr / atr_avg - 1.5) * 0.5, 0.9)
                 reason = "High volatility expansion in bearish direction"
        elif curr_atr < atr_avg * 0.5:
             reason = "Volatility contraction, anticipating breakout"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "atr_14": float(curr_atr),
                "atr_avg_20": float(atr_avg)
            }
        }
