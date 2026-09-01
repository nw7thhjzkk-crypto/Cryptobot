import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_rsi, calculate_bbands, calculate_adx
from bot.config import MEAN_REVERSION_ELIGIBLE

class MeanReversionAgent(BaseAgent):
    def __init__(self):
        super().__init__("MeanReversionAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if symbol not in MEAN_REVERSION_ELIGIBLE:
            return self._create_hold_signal(symbol, "Symbol not eligible for mean reversion")

        if len(price_history) < 40:
            return self._create_hold_signal(symbol, "Insufficient data for mean reversion")

        df = price_history.copy()
        rsi = calculate_rsi(df, length=14)
        lower_band, mid_band, upper_band, bb_width = calculate_bbands(df, length=20)
        adx = calculate_adx(df, length=14)

        if rsi is None or rsi.empty or lower_band.empty or upper_band.empty or adx.empty:
            return self._create_hold_signal(symbol, "Failed to calculate indicators")

        curr_rsi = float(rsi.iloc[-1])
        curr_close = float(df['close'].iloc[-1])
        curr_lower = float(lower_band.iloc[-1])
        curr_upper = float(upper_band.iloc[-1])
        curr_mid = float(mid_band.iloc[-1])
        curr_bb_width = float(bb_width.iloc[-1])
        bb_width_avg = float(bb_width.rolling(window=20).mean().iloc[-1])
        curr_adx = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 25.0

        # Volume
        vol_avg = df['volume'].rolling(window=20).mean().iloc[-1] if 'volume' in df.columns else 1.0
        curr_vol = float(df['volume'].iloc[-1]) if 'volume' in df.columns else 1.0
        rel_vol = curr_vol / vol_avg if vol_avg > 0 else 1.0

        # Only trade mean reversion in low-trend (ranging) environments
        if curr_adx > 25:
            return self._create_hold_signal(
                symbol,
                f"ADX too high ({curr_adx:.1f}) - not suitable for mean reversion",
                features={"adx": curr_adx, "rsi": curr_rsi}
            )

        # Avoid expanding volatility
        if curr_bb_width > bb_width_avg * 1.6:
            return self._create_hold_signal(symbol, "Bollinger bands expanding rapidly - avoid mean reversion")

        signal = "HOLD"
        confidence = 0.0
        reason = "Price within normal bounds"

        if curr_rsi < 28 and curr_close <= curr_lower * 1.005:
            signal = "BUY"
            dist_to_mid = (curr_mid - curr_close) / curr_close if curr_close > 0 else 0
            confidence = min(0.55 + (30 - curr_rsi) / 25.0 + dist_to_mid * 4, 0.92)
            reason = f"Oversold RSI ({curr_rsi:.1f}) + lower BB touch"
            if rel_vol > 1.2:
                confidence = min(confidence + 0.08, 0.95)
                reason += " + volume"

        elif curr_rsi > 72 and curr_close >= curr_upper * 0.995:
            signal = "SELL"
            dist_to_mid = (curr_close - curr_mid) / curr_close if curr_close > 0 else 0
            confidence = min(0.55 + (curr_rsi - 70) / 25.0 + dist_to_mid * 4, 0.92)
            reason = f"Overbought RSI ({curr_rsi:.1f}) + upper BB touch"
            if rel_vol > 1.2:
                confidence = min(confidence + 0.08, 0.95)
                reason += " + volume"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": float(score),
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "rsi_14": curr_rsi,
                "lower_band": curr_lower,
                "upper_band": curr_upper,
                "bb_width": curr_bb_width,
                "adx": curr_adx,
                "rel_vol": float(rel_vol)
            }
        }
