import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_rsi, calculate_bbands
from bot.config import MEAN_REVERSION_ELIGIBLE

class MeanReversionAgent(BaseAgent):
    def __init__(self):
        super().__init__("MeanReversionAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if symbol not in MEAN_REVERSION_ELIGIBLE:
            return self._create_hold_signal(symbol, "Symbol not eligible for mean reversion")

        if len(price_history) < 25:
            return self._create_hold_signal(symbol, "Insufficient data for mean reversion")

        df = price_history.copy()
        rsi = calculate_rsi(df, length=14)
        lower_band, mid_band, upper_band, bb_width = calculate_bbands(df, length=20)

        if rsi is None or rsi.empty or lower_band.empty or upper_band.empty:
             return self._create_hold_signal(symbol, "Failed to calculate indicators")

        curr_rsi = rsi.iloc[-1]
        curr_close = df['close'].iloc[-1]
        curr_lower = lower_band.iloc[-1]
        curr_upper = upper_band.iloc[-1]
        curr_mid = mid_band.iloc[-1]

        signal = "HOLD"
        confidence = 0.0
        reason = "Price within normal bounds"

        curr_bb_width = bb_width.iloc[-1]
        bb_width_avg = bb_width.rolling(window=20).mean().iloc[-1]

        if curr_bb_width > bb_width_avg * 1.5:
            return self._create_hold_signal(symbol, "Bands expanding rapidly, avoiding mean reversion")

        if curr_rsi < 30 and curr_close <= curr_lower:
            signal = "BUY"
            dist_to_mid = (curr_mid - curr_close) / curr_close
            confidence = min(0.6 + (30 - curr_rsi)/20.0 + (dist_to_mid * 5), 1.0)
            reason = "Oversold RSI and price at/below lower band"
        elif curr_rsi > 70 and curr_close >= curr_upper:
            signal = "SELL"
            dist_to_mid = (curr_close - curr_mid) / curr_close
            confidence = min(0.6 + (curr_rsi - 70)/20.0 + (dist_to_mid * 5), 1.0)
            reason = "Overbought RSI and price at/above upper band"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "rsi_14": float(curr_rsi),
                "lower_band": float(curr_lower),
                "upper_band": float(curr_upper),
                "bb_width": float(curr_bb_width)
            }
        }
