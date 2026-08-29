import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent

class VolumeAgent(BaseAgent):
    def __init__(self):
        super().__init__("VolumeAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 25:
            return self._create_hold_signal(symbol, "Insufficient data for volume analysis")

        df = price_history.copy()

        vol_avg = df['volume'].rolling(window=20).mean()

        if vol_avg.empty:
            return self._create_hold_signal(symbol, "Failed to calculate volume average")

        curr_vol = df['volume'].iloc[-1]
        curr_vol_avg = vol_avg.iloc[-1]

        if curr_vol_avg <= 0:
            return self._create_hold_signal(symbol, "Invalid volume average")

        rvol = curr_vol / curr_vol_avg

        curr_close = df['close'].iloc[-1]
        curr_open = df['open'].iloc[-1]
        prev_close = df['close'].iloc[-2]

        is_bullish_bar = curr_close > curr_open and curr_close > prev_close
        is_bearish_bar = curr_close < curr_open and curr_close < prev_close

        signal = "HOLD"
        confidence = 0.0
        reason = "Normal volume"

        if rvol > 2.0:
            if is_bullish_bar:
                signal = "BUY"
                confidence = min(0.5 + (rvol - 2.0) * 0.2, 0.95)
                reason = f"Significant bullish volume influx (RVOL {rvol:.2f})"
            elif is_bearish_bar:
                signal = "SELL"
                confidence = min(0.5 + (rvol - 2.0) * 0.2, 0.95)
                reason = f"Significant bearish volume selling pressure (RVOL {rvol:.2f})"
            else:
                 reason = f"High volume (RVOL {rvol:.2f}) but indecisive price action"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "relative_volume": float(rvol),
                "volume_avg": float(curr_vol_avg)
            }
        }
