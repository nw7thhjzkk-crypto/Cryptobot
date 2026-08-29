import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent

class BreakoutAgent(BaseAgent):
    def __init__(self):
        super().__init__("BreakoutAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        lookback = 20
        if len(price_history) < lookback + 5:
            return self._create_hold_signal(symbol, "Insufficient data for breakout analysis")

        df = price_history.copy()

        rolling_high = df['high'].shift(1).rolling(window=lookback).max()
        rolling_low = df['low'].shift(1).rolling(window=lookback).min()
        vol_avg = df['volume'].rolling(window=20).mean()

        if rolling_high.empty or rolling_low.empty or vol_avg.empty:
            return self._create_hold_signal(symbol, "Failed to calculate indicators")

        curr_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        curr_vol = df['volume'].iloc[-1]
        curr_vol_avg = vol_avg.iloc[-1]

        curr_high_level = rolling_high.iloc[-1]
        curr_low_level = rolling_low.iloc[-1]

        signal = "HOLD"
        confidence = 0.0
        reason = "Price within range"

        if curr_vol_avg > 0:
            rel_vol = curr_vol / curr_vol_avg
        else:
            rel_vol = 1.0

        if curr_close > curr_high_level and prev_close <= curr_high_level:
            if rel_vol > 1.2:
                signal = "BUY"
                confidence = min(0.6 + (rel_vol - 1.2) * 0.2, 0.95)
                reason = "Price broke above 20-period high with volume confirmation"
            else:
                reason = "Breakout above high, but insufficient volume"
        elif curr_close < curr_low_level and prev_close >= curr_low_level:
            if rel_vol > 1.2:
                signal = "SELL"
                confidence = min(0.6 + (rel_vol - 1.2) * 0.2, 0.95)
                reason = "Price broke below 20-period low with volume confirmation"
            else:
                reason = "Breakout below low, but insufficient volume"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "rolling_high": float(curr_high_level),
                "rolling_low": float(curr_low_level),
                "relative_volume": float(rel_vol)
            }
        }
