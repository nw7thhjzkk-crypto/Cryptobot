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

        curr_close = float(df['close'].iloc[-1])
        prev_close = float(df['close'].iloc[-2])
        curr_vol = float(df['volume'].iloc[-1])
        curr_vol_avg = float(vol_avg.iloc[-1])

        curr_high_level = float(rolling_high.iloc[-1])
        curr_low_level = float(rolling_low.iloc[-1])

        rel_vol = curr_vol / curr_vol_avg if curr_vol_avg > 0 else 1.0

        signal = "HOLD"
        confidence = 0.0
        reason = "Price within range"

        # Bullish breakout
        if curr_close > curr_high_level and prev_close <= curr_high_level:
            if rel_vol >= 1.4:
                signal = "BUY"
                confidence = min(0.58 + (rel_vol - 1.4) * 0.18, 0.93)
                reason = f"Breakout above {lookback}-bar high with volume (RVOL {rel_vol:.2f})"
            else:
                reason = f"Breakout above high but weak volume (RVOL {rel_vol:.2f})"

        # Bearish breakout
        elif curr_close < curr_low_level and prev_close >= curr_low_level:
            if rel_vol >= 1.4:
                signal = "SELL"
                confidence = min(0.58 + (rel_vol - 1.4) * 0.18, 0.93)
                reason = f"Breakdown below {lookback}-bar low with volume (RVOL {rel_vol:.2f})"
            else:
                reason = f"Breakdown below low but weak volume (RVOL {rel_vol:.2f})"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": float(score),
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "rolling_high": curr_high_level,
                "rolling_low": curr_low_level,
                "relative_volume": float(rel_vol)
            }
        }
