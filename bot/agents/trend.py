import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.factors import calculate_macd, calculate_adx, calculate_atr

class TrendAgent(BaseAgent):
    def __init__(self):
        super().__init__("TrendAgent", version="1.1", parameters={"macd_fast": 12, "macd_slow": 26, "adx_length": 14}, regime_compatibility=["trending_bull", "trending_bear", "transitional"])

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 35:
            return self._create_hold_signal(symbol, "Insufficient data for Trend Agent")

        df = price_history.copy()

        macd_line, signal_line, hist = calculate_macd(df, fast=self.parameters["macd_fast"], slow=self.parameters["macd_slow"])
        adx = calculate_adx(df, length=self.parameters["adx_length"])

        if macd_line is None or adx is None or adx.empty:
            return self._create_hold_signal(symbol, "Failed to calculate Trend indicators")

        curr_macd = float(macd_line.iloc[-1])
        curr_sig = float(signal_line.iloc[-1])
        prev_macd = float(macd_line.iloc[-2])
        prev_sig = float(signal_line.iloc[-2])

        curr_adx = float(adx.iloc[-1])

        signal = "HOLD"
        confidence = 0.0
        reason = "No clear trend setup"

        # Basic MACD Crossover with ADX confirmation
        if curr_macd > curr_sig and prev_macd <= prev_sig and curr_adx > 25:
            signal = "BUY"
            confidence = min(0.6 + (curr_adx - 25) / 100, 0.95)
            reason = f"MACD Bullish Cross + ADX>25 ({curr_adx:.1f})"

        elif curr_macd < curr_sig and prev_macd >= prev_sig and curr_adx > 25:
            signal = "SELL"
            confidence = min(0.6 + (curr_adx - 25) / 100, 0.95)
            reason = f"MACD Bearish Cross + ADX>25 ({curr_adx:.1f})"

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
                "macd": curr_macd,
                "macd_signal": curr_sig,
                "adx_14": curr_adx
            }
        }
