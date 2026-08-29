import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_rsi

class MomentumAgent(BaseAgent):
    def __init__(self):
        super().__init__("MomentumAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 20:
            return self._create_hold_signal(symbol, "Insufficient data for momentum analysis")

        df = price_history.copy()
        rsi = calculate_rsi(df, length=14)

        roc_period = 10
        if len(df) > roc_period:
            roc = ((df['close'] - df['close'].shift(roc_period)) / df['close'].shift(roc_period)) * 100
        else:
            roc = pd.Series([0.0]*len(df))

        if rsi is None or rsi.empty or roc.empty:
            return self._create_hold_signal(symbol, "Failed to calculate indicators")

        curr_rsi = rsi.iloc[-1]
        curr_roc = roc.iloc[-1]

        signal = "HOLD"
        confidence = 0.0
        reason = "Neutral momentum"

        if curr_rsi > 70 and curr_roc < 0:
            signal = "SELL"
            confidence = min(0.5 + (curr_rsi - 70) / 30.0, 0.9)
            reason = "Overbought RSI with negative momentum (ROC)"
        elif curr_rsi < 30 and curr_roc > 0:
            signal = "BUY"
            confidence = min(0.5 + (30 - curr_rsi) / 30.0, 0.9)
            reason = "Oversold RSI with positive momentum (ROC)"
        elif curr_rsi > 50 and curr_roc > 2.0:
            signal = "BUY"
            confidence = min(0.4 + (curr_roc / 10.0), 0.8)
            reason = "Positive momentum in bullish RSI zone"
        elif curr_rsi < 50 and curr_roc < -2.0:
            signal = "SELL"
            confidence = min(0.4 + (abs(curr_roc) / 10.0), 0.8)
            reason = "Negative momentum in bearish RSI zone"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "rsi_14": float(curr_rsi),
                "roc_10": float(curr_roc)
            }
        }
