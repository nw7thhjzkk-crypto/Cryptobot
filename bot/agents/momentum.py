import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_rsi

class MomentumAgent(BaseAgent):
    def __init__(self):
        super().__init__("MomentumAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 25:
            return self._create_hold_signal(symbol, "Insufficient data for momentum analysis")

        df = price_history.copy()
        rsi = calculate_rsi(df, length=14)

        roc_period = 10
        roc = ((df['close'] - df['close'].shift(roc_period)) / df['close'].shift(roc_period)) * 100

        if rsi is None or rsi.empty or roc.empty:
            return self._create_hold_signal(symbol, "Failed to calculate indicators")

        curr_rsi = float(rsi.iloc[-1])
        curr_roc = float(roc.iloc[-1])
        prev_roc = float(roc.iloc[-2]) if len(roc) > 1 else 0.0

        signal = "HOLD"
        confidence = 0.0
        reason = "Neutral momentum"

        # Strong momentum continuation
        if curr_rsi > 55 and curr_roc > 3.0 and curr_roc > prev_roc:
            signal = "BUY"
            confidence = min(0.45 + (curr_roc / 12.0) + (curr_rsi - 50) / 40.0, 0.88)
            reason = f"Positive momentum acceleration (ROC {curr_roc:.1f}%, RSI {curr_rsi:.1f})"

        elif curr_rsi < 45 and curr_roc < -3.0 and curr_roc < prev_roc:
            signal = "SELL"
            confidence = min(0.45 + (abs(curr_roc) / 12.0) + (50 - curr_rsi) / 40.0, 0.88)
            reason = f"Negative momentum acceleration (ROC {curr_roc:.1f}%, RSI {curr_rsi:.1f})"

        # Extreme mean-reversion style momentum fade
        elif curr_rsi > 75 and curr_roc < 0:
            signal = "SELL"
            confidence = min(0.5 + (curr_rsi - 75) / 25.0, 0.85)
            reason = f"Overbought RSI with fading momentum (RSI {curr_rsi:.1f})"

        elif curr_rsi < 25 and curr_roc > 0:
            signal = "BUY"
            confidence = min(0.5 + (25 - curr_rsi) / 25.0, 0.85)
            reason = f"Oversold RSI with improving momentum (RSI {curr_rsi:.1f})"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": float(score),
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "rsi_14": curr_rsi,
                "roc_10": curr_roc
            }
        }
