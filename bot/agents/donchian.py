import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent

class DonchianBreakoutAgent(BaseAgent):
    def __init__(self, entry_lookback: int = 20, exit_lookback: int = 10):
        super().__init__("DonchianBreakoutAgent")
        self.entry_lookback = entry_lookback
        self.exit_lookback = exit_lookback

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < max(self.entry_lookback, self.exit_lookback) + 5:
            return self._create_hold_signal(symbol, "Insufficient data for Donchian breakout")

        df = price_history.copy()

        # Donchian upper channel for entry (delayed by 1 to prevent look-ahead bias)
        donchian_high = df['high'].shift(1).rolling(window=self.entry_lookback).max()
        # Donchian lower channel for entry
        donchian_low = df['low'].shift(1).rolling(window=self.entry_lookback).min()

        # Fast exits
        exit_high = df['high'].shift(1).rolling(window=self.exit_lookback).max()
        exit_low = df['low'].shift(1).rolling(window=self.exit_lookback).min()

        if donchian_high.empty or donchian_low.empty:
            return self._create_hold_signal(symbol, "Failed to calculate Donchian channels")

        curr_close = float(df['close'].iloc[-1])
        dh_val = float(donchian_high.iloc[-1])
        dl_val = float(donchian_low.iloc[-1])
        eh_val = float(exit_high.iloc[-1])
        el_val = float(exit_low.iloc[-1])

        signal = "HOLD"
        confidence = 0.0
        reason = "Price within Donchian channel"

        if curr_close > dh_val:
            signal = "BUY"
            confidence = min(0.6 + (curr_close - dh_val) / dh_val * 10, 0.95)
            reason = f"Bullish breakout above {self.entry_lookback}-period Donchian High"
        elif curr_close < dl_val:
            signal = "SELL"
            confidence = min(0.6 + (dl_val - curr_close) / dl_val * 10, 0.95)
            reason = f"Bearish breakout below {self.entry_lookback}-period Donchian Low"

        # If we are holding a long, and price falls below the fast exit low, we want to SELL (or vice versa for shorts).
        # But this agent operates as a stateless signal generator, so we will generate a weak reversal signal
        # that functions as an exit if held.
        elif curr_close < el_val:
            signal = "SELL"
            confidence = 0.45
            reason = f"Price below {self.exit_lookback}-period fast exit low (momentum fading)"
        elif curr_close > eh_val:
            signal = "BUY"
            confidence = 0.45
            reason = f"Price above {self.exit_lookback}-period fast exit high (momentum fading)"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": float(score),
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "donchian_high": dh_val,
                "donchian_low": dl_val,
                "exit_high": eh_val,
                "exit_low": el_val
            }
        }
