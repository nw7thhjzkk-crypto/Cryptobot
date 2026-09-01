import pandas as pd
import numpy as np
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_atr, calculate_adx

class MarketRegimeAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketRegimeAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 200:
            return self._create_hold_signal(symbol, "Insufficient data for regime analysis (needs ~200 bars)")

        df = price_history.copy()

        # Core indicators
        sma50 = df['close'].rolling(window=50).mean()
        sma200 = df['close'].rolling(window=200).mean()
        atr = calculate_atr(df, length=14)
        adx = calculate_adx(df, length=14)

        if sma50.empty or sma200.empty or atr.empty or adx.empty:
            return self._create_hold_signal(symbol, "Failed to calculate regime indicators")

        curr_close = float(df['close'].iloc[-1])
        curr_sma50 = float(sma50.iloc[-1])
        curr_sma200 = float(sma200.iloc[-1])
        curr_atr = float(atr.iloc[-1])
        atr_50_avg = float(atr.rolling(window=50).mean().iloc[-1]) if not atr.rolling(window=50).mean().empty else curr_atr
        curr_adx = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0.0

        # Volatility regime
        is_high_vol = curr_atr > (atr_50_avg * 1.4) if atr_50_avg > 0 else False

        # Trend structure
        is_bullish_structure = curr_close > curr_sma50 > curr_sma200
        is_bearish_structure = curr_close < curr_sma50 < curr_sma200

        # Final regime decision (professional style)
        regime = "sideways"
        score = 0.0
        confidence = 0.5

        if curr_adx >= 25:
            # Strong trend
            if is_bullish_structure:
                regime = "trending_bull"
                score = 0.85
                confidence = min(0.6 + (curr_adx - 25) / 50.0, 0.95)
            elif is_bearish_structure:
                regime = "trending_bear"
                score = -0.85
                confidence = min(0.6 + (curr_adx - 25) / 50.0, 0.95)
            else:
                regime = "trending"
                score = 0.3 if curr_close > curr_sma50 else -0.3
                confidence = 0.55
        elif curr_adx < 20:
            # Low trend strength → ranging / mean-reversion friendly
            regime = "ranging"
            score = 0.0
            confidence = 0.7
        else:
            # Transitional
            regime = "transitional"
            score = 0.1 if is_bullish_structure else (-0.1 if is_bearish_structure else 0.0)
            confidence = 0.45

        # High volatility override (risk-off bias)
        if is_high_vol:
            if regime in ("trending_bear", "transitional") or score < 0:
                regime = "risk_off"
                score = -1.0
                confidence = 0.9
            else:
                regime = f"{regime}_high_vol"
                confidence = max(confidence - 0.15, 0.3)

        reason = f"Regime={regime} | ADX={curr_adx:.1f} | ATR ratio={curr_atr/atr_50_avg:.2f}" if atr_50_avg > 0 else f"Regime={regime} | ADX={curr_adx:.1f}"

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": "HOLD",  # Regime agent does not trade by itself
            "score": float(score),
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "regime": regime,
                "adx": curr_adx,
                "sma50": curr_sma50,
                "sma200": curr_sma200,
                "atr": curr_atr,
                "high_volatility": is_high_vol
            }
        }
