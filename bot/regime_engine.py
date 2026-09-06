import pandas as pd
from typing import Dict, Any
from bot.factors import calculate_adx, calculate_atr

class MarketRegimeEngine:
    def __init__(self, adx_period: int = 14, sma_fast: int = 20, sma_slow: int = 50, atr_period: int = 14):
        self.adx_period = adx_period
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow
        self.atr_period = atr_period

    def analyze(self, symbol: str, price_history: pd.DataFrame) -> Dict[str, Any]:
        """
        Determines the market regime.
        Returns regime string and confidence.
        """
        if len(price_history) < max(self.sma_slow, self.adx_period * 2):
            return {"regime": "unknown", "confidence": 0.0, "reason": "Insufficient data"}

        df = price_history.copy()

        # Factors
        adx = calculate_adx(df, length=self.adx_period)
        atr = calculate_atr(df, length=self.atr_period)
        sma_f = df['close'].rolling(window=self.sma_fast).mean()
        sma_s = df['close'].rolling(window=self.sma_slow).mean()

        import numpy as np
        if adx is None or adx.empty or atr.empty or sma_s.empty or np.isnan(adx.iloc[-1]) or np.isnan(atr.iloc[-1]) or float(atr.iloc[-1]) < 0 or float(adx.iloc[-1]) < 0:
            return {"regime": "unknown", "confidence": 0.0, "reason": "Calculation failed or NaN"}

        curr_adx = float(adx.iloc[-1])
        curr_atr = float(atr.iloc[-1])
        curr_close = float(df['close'].iloc[-1])
        curr_sma_f = float(sma_f.iloc[-1])
        curr_sma_s = float(sma_s.iloc[-1])

        # Volatility baseline (using 50-day average ATR)
        avg_atr = float(atr.iloc[-50:].mean()) if len(atr) >= 50 else curr_atr
        vol_ratio = curr_atr / avg_atr if avg_atr > 0 else 1.0

        regime = "transitional"
        confidence = 0.5
        reason = "No strong regime detected"

        # High Volatility overriding regime
        if vol_ratio > 2.0:
            regime = "high_volatility"
            confidence = min(vol_ratio / 4.0, 0.9)
            reason = f"Volatility spike (ATR ratio {vol_ratio:.1f}x)"

        # Risk-off (severe drop)
        elif curr_close < curr_sma_s * 0.85:
            regime = "risk_off"
            confidence = 0.85
            reason = "Price >15% below 50-SMA"

        # Trending environments
        elif curr_adx > 25:
            if curr_sma_f > curr_sma_s and curr_close > curr_sma_f:
                regime = "trending_bull"
                confidence = min(0.6 + (curr_adx - 25) / 50.0, 0.95)
                reason = f"Strong uptrend (ADX {curr_adx:.1f}, Price > Fast SMA > Slow SMA)"
            elif curr_sma_f < curr_sma_s and curr_close < curr_sma_f:
                regime = "trending_bear"
                confidence = min(0.6 + (curr_adx - 25) / 50.0, 0.95)
                reason = f"Strong downtrend (ADX {curr_adx:.1f}, Price < Fast SMA < Slow SMA)"

        # Ranging
        elif curr_adx < 20:
            regime = "ranging"
            confidence = min(0.6 + (20 - curr_adx) / 20.0, 0.9)
            reason = f"Weak trend (ADX {curr_adx:.1f})"

        return {
            "regime": regime,
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "adx_14": curr_adx,
                "atr_ratio": vol_ratio,
                "sma_fast": curr_sma_f,
                "sma_slow": curr_sma_s
            }
        }
