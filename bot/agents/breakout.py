import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.factors import calculate_atr

class BreakoutAgent(BaseAgent):
    def __init__(self, lookback: int = 20):
        super().__init__("BreakoutAgent", version="1.1", parameters={"lookback": lookback}, regime_compatibility=["trending_bull", "trending_bear", "ranging"])
        self.lookback = lookback

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < self.lookback + 5:
            return self._create_hold_signal(symbol, "Insufficient data for Breakout Agent")

        df = price_history.copy()

        recent_high = df['high'].iloc[-self.lookback-1:-1].max()
        recent_low = df['low'].iloc[-self.lookback-1:-1].min()

        curr_close = float(df['close'].iloc[-1])
        curr_vol = float(df['volume'].iloc[-1])
        avg_vol = df['volume'].iloc[-self.lookback-1:-1].mean()

        signal = "HOLD"
        confidence = 0.0
        reason = "Price within recent range"

        # Check for volume confirmation
        vol_multiplier = curr_vol / avg_vol if avg_vol > 0 else 0

        if curr_close > recent_high:
            signal = "BUY"
            confidence = min(0.5 + (vol_multiplier * 0.1), 0.95)
            reason = f"Breakout above {self.lookback}-bar high with {vol_multiplier:.1f}x volume"
        elif curr_close < recent_low:
            signal = "SELL"
            confidence = min(0.5 + (vol_multiplier * 0.1), 0.95)
            reason = f"Breakdown below {self.lookback}-bar low with {vol_multiplier:.1f}x volume"

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
                "recent_high": float(recent_high),
                "recent_low": float(recent_low),
                "vol_multiplier": float(vol_multiplier)
            }
        }
