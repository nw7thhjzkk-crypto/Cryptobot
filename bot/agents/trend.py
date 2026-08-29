import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_macd

class TrendAgent(BaseAgent):
    def __init__(self):
        super().__init__("TrendAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 60:
            return self._create_hold_signal(symbol, "Insufficient data for trend analysis")

        df = price_history.copy()
        ema20 = df['close'].ewm(span=20, adjust=False).mean()
        ema50 = df['close'].ewm(span=50, adjust=False).mean()
        macd_hist = calculate_macd(df)

        if ema20.empty or ema50.empty or macd_hist.empty:
             return self._create_hold_signal(symbol, "Failed to calculate indicators")

        prev_ema20, curr_ema20 = ema20.iloc[-2], ema20.iloc[-1]
        prev_ema50, curr_ema50 = ema50.iloc[-2], ema50.iloc[-1]
        curr_macd_hist = macd_hist.iloc[-1]

        cross_above = prev_ema20 <= prev_ema50 and curr_ema20 > curr_ema50
        cross_below = prev_ema20 >= prev_ema50 and curr_ema20 < curr_ema50

        dist_pct = (curr_ema20 - curr_ema50) / curr_ema50
        signal = "HOLD"
        confidence = 0.0
        reason = "No clear trend signal"

        if curr_ema20 > curr_ema50:
            if curr_macd_hist > 0:
                signal = "BUY"
                confidence = min(0.5 + abs(dist_pct) * 10, 1.0)
                reason = "EMA20 above EMA50, supported by MACD"
                if cross_above:
                    confidence = min(confidence + 0.3, 1.0)
                    reason = "Bullish EMA crossover confirmed by MACD"
        elif curr_ema20 < curr_ema50:
             if curr_macd_hist < 0:
                signal = "SELL"
                confidence = min(0.5 + abs(dist_pct) * 10, 1.0)
                reason = "EMA20 below EMA50, supported by MACD"
                if cross_below:
                    confidence = min(confidence + 0.3, 1.0)
                    reason = "Bearish EMA crossover confirmed by MACD"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "ema20": float(curr_ema20),
                "ema50": float(curr_ema50),
                "macd_hist": float(curr_macd_hist)
            }
        }
