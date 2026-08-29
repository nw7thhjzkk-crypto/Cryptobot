import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_atr

class MarketRegimeAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketRegimeAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 200:
            return self._create_hold_signal(symbol, "Insufficient data for regime analysis (needs 200 bars)")

        df = price_history.copy()

        sma50 = df['close'].rolling(window=50).mean()
        sma200 = df['close'].rolling(window=200).mean()
        atr = calculate_atr(df, length=14)

        if sma50.empty or sma200.empty or atr.empty:
            return self._create_hold_signal(symbol, "Failed to calculate indicators")

        curr_close = df['close'].iloc[-1]
        curr_sma50 = sma50.iloc[-1]
        curr_sma200 = sma200.iloc[-1]

        curr_atr = atr.iloc[-1]
        atr_avg = atr.rolling(window=50).mean().iloc[-1]

        regime = "sideways"
        score = 0.0

        is_bullish = curr_close > curr_sma50 and curr_sma50 > curr_sma200
        is_bearish = curr_close < curr_sma50 and curr_sma50 < curr_sma200
        is_high_vol = curr_atr > atr_avg * 1.5

        if is_bullish:
            regime = "bullish"
            score = 0.8
        elif is_bearish:
            regime = "bearish"
            score = -0.8

        if is_high_vol:
            regime = f"{regime}/high_volatility" if regime != "sideways" else "high_volatility"
            if is_bearish:
                regime = "risk-off"
                score = -1.0

        reason = f"Market regime detected as {regime}"

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": "HOLD",
            "score": score,
            "confidence": abs(score),
            "reason": reason,
            "features": {
                "regime": regime,
                "sma50": float(curr_sma50),
                "sma200": float(curr_sma200),
                "high_volatility": is_high_vol
            }
        }
