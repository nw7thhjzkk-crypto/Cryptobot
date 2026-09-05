import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent

class DonchianBreakoutAgent(BaseAgent):
    def __init__(self, entry_lookback: int = 20, exit_lookback: int = 10):
        super().__init__("DonchianBreakoutAgent", version="1.1", parameters={"entry_lookback": entry_lookback, "exit_lookback": exit_lookback}, regime_compatibility=["trending_bull", "trending_bear"])
        self.entry_lookback = entry_lookback
        self.exit_lookback = exit_lookback

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < max(self.entry_lookback, self.exit_lookback) + 5:
            return self._create_hold_signal(symbol, "Insufficient data for Donchian analysis")

        df = price_history.copy()

        # Donchian Channels (using previous periods to avoid lookahead bias)
        recent_high = df['high'].iloc[-self.entry_lookback-1:-1].max()
        recent_low = df['low'].iloc[-self.entry_lookback-1:-1].min()

        exit_high = df['high'].iloc[-self.exit_lookback-1:-1].max()
        exit_low = df['low'].iloc[-self.exit_lookback-1:-1].min()

        curr_close = float(df['close'].iloc[-1])

        signal = "HOLD"
        confidence = 0.0
        reason = "Price within Donchian channel"

        # Entry logic
        if curr_close > recent_high:
            signal = "BUY"
            confidence = 0.8
            reason = f"Breakout above {self.entry_lookback}-period Donchian high ({recent_high:.2f})"
        elif curr_close < recent_low:
            signal = "SELL"
            confidence = 0.8
            reason = f"Breakdown below {self.entry_lookback}-period Donchian low ({recent_low:.2f})"

        # Exit logic (for existing positions, represented as reverse signal with high confidence)
        # Note: In a full system, exits might be handled by the execution/risk engine.
        # Here we emit strong opposing signals if exit conditions are met.
        if signal == "HOLD":
             if curr_close < exit_low:
                 signal = "SELL"
                 confidence = 0.9 # High confidence to force exit of longs
                 reason = f"Price below {self.exit_lookback}-period Donchian exit low ({exit_low:.2f})"
             elif curr_close > exit_high:
                 signal = "BUY"
                 confidence = 0.9 # High confidence to force exit of shorts
                 reason = f"Price above {self.exit_lookback}-period Donchian exit high ({exit_high:.2f})"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "version": self.version,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "entry_high": float(recent_high),
                "entry_low": float(recent_low),
                "exit_high": float(exit_high),
                "exit_low": float(exit_low)
            }
        }
