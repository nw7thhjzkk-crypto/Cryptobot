import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.factors import calculate_bbands, calculate_rsi
from bot.config import MEAN_REVERSION_ELIGIBLE

class MeanReversionAgent(BaseAgent):
    def __init__(self):
        super().__init__("MeanReversionAgent", version="1.1", parameters={"bb_length": 20, "bb_std": 2.0, "rsi_length": 14}, regime_compatibility=["ranging", "transitional"])

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if not MEAN_REVERSION_ELIGIBLE:
             return self._create_hold_signal(symbol, "Mean reversion disabled in config")

        if len(price_history) < max(self.parameters["bb_length"], self.parameters["rsi_length"]) + 5:
            return self._create_hold_signal(symbol, "Insufficient data for MR Agent")

        df = price_history.copy()

        lower, sma, upper = calculate_bbands(df, length=self.parameters["bb_length"], std=self.parameters["bb_std"])
        rsi = calculate_rsi(df, length=self.parameters["rsi_length"])

        if lower is None or rsi is None or rsi.empty:
             return self._create_hold_signal(symbol, "Indicator calculation failed")

        curr_close = float(df['close'].iloc[-1])
        curr_lower = float(lower.iloc[-1])
        curr_upper = float(upper.iloc[-1])
        curr_rsi = float(rsi.iloc[-1])

        signal = "HOLD"
        confidence = 0.0
        reason = "Price within normal bounds"

        if curr_close < curr_lower and curr_rsi < 30:
            signal = "BUY"
            confidence = min(0.6 + (30 - curr_rsi) / 30.0, 0.90)
            reason = f"Price below lower BB + Oversold RSI ({curr_rsi:.1f})"

        elif curr_close > curr_upper and curr_rsi > 70:
            signal = "SELL"
            confidence = min(0.6 + (curr_rsi - 70) / 30.0, 0.90)
            reason = f"Price above upper BB + Overbought RSI ({curr_rsi:.1f})"

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
                "bb_lower": curr_lower,
                "bb_upper": curr_upper
            }
        }
