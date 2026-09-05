import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.factors import calculate_rsi

class MomentumAgent(BaseAgent):
    def __init__(self):
        super().__init__("MomentumAgent", version="1.1", parameters={"rsi_length": 14, "roc_length": 10}, regime_compatibility=["trending_bull", "trending_bear"])

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < max(self.parameters["rsi_length"], self.parameters["roc_length"]) + 5:
            return self._create_hold_signal(symbol, "Insufficient data for Momentum Agent")

        df = price_history.copy()

        rsi = calculate_rsi(df, length=self.parameters["rsi_length"])
        if rsi is None or rsi.empty:
            return self._create_hold_signal(symbol, "RSI calculation failed")

        curr_rsi = float(rsi.iloc[-1])

        # Rate of Change (ROC)
        roc_len = self.parameters["roc_length"]
        curr_roc = (df['close'].iloc[-1] - df['close'].iloc[-roc_len-1]) / df['close'].iloc[-roc_len-1] * 100
        prev_roc = (df['close'].iloc[-2] - df['close'].iloc[-roc_len-2]) / df['close'].iloc[-roc_len-2] * 100

        signal = "HOLD"
        confidence = 0.0
        reason = "Momentum is flat or conflicting"

        # Strong accelerating momentum
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
            "version": self.version,
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
