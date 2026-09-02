import pandas as pd
import numpy as np
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_atr, calculate_adx


def _normalize_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """Alpaca sometimes returns capitalized column names."""
    out = df.copy()
    rename = {}
    for c in out.columns:
        cl = str(c).lower()
        if cl in ("open", "high", "low", "close", "volume", "trade_count", "vwap"):
            rename[c] = cl
    if rename:
        out = out.rename(columns=rename)
    return out


class MarketRegimeAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketRegimeAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if price_history is None or len(price_history) < 40:
            return self._create_hold_signal(
                symbol,
                f"Insufficient data for regime ({0 if price_history is None else len(price_history)} bars)",
                features={"regime": "unknown"},
            )

        df = _normalize_ohlc(price_history)
        if "close" not in df.columns:
            return self._create_hold_signal(
                symbol, "Missing close column in price history",
                features={"regime": "unknown"},
            )

        n = len(df)
        # Adaptive windows based on available history
        w_fast = min(20, max(5, n // 4))
        w_mid = min(50, max(10, n // 3))
        w_slow = min(200, max(20, n - 5))

        sma_fast = df["close"].rolling(window=w_fast).mean()
        sma_mid = df["close"].rolling(window=w_mid).mean()
        sma_slow = df["close"].rolling(window=w_slow).mean()

        atr = calculate_atr(df, length=min(14, max(5, n // 5)))
        adx = calculate_adx(df, length=min(14, max(5, n // 5)))

        curr_close = float(df["close"].iloc[-1])
        curr_sma_fast = float(sma_fast.iloc[-1]) if not pd.isna(sma_fast.iloc[-1]) else curr_close
        curr_sma_mid = float(sma_mid.iloc[-1]) if not pd.isna(sma_mid.iloc[-1]) else curr_close
        curr_sma_slow = float(sma_slow.iloc[-1]) if not pd.isna(sma_slow.iloc[-1]) else curr_close

        curr_atr = float(atr.iloc[-1]) if atr is not None and not atr.empty and not pd.isna(atr.iloc[-1]) else 0.0
        atr_avg = float(atr.rolling(window=min(50, len(atr))).mean().iloc[-1]) if atr is not None and len(atr) > 5 else curr_atr
        curr_adx = float(adx.iloc[-1]) if adx is not None and not adx.empty and not pd.isna(adx.iloc[-1]) else 0.0

        is_high_vol = curr_atr > (atr_avg * 1.4) if atr_avg > 0 else False
        is_bullish = curr_close > curr_sma_mid > curr_sma_slow
        is_bearish = curr_close < curr_sma_mid < curr_sma_slow

        regime = "sideways"
        score = 0.0
        confidence = 0.5

        if curr_adx >= 25:
            if is_bullish:
                regime = "trending_bull"
                score = 0.85
                confidence = min(0.6 + (curr_adx - 25) / 50.0, 0.95)
            elif is_bearish:
                regime = "trending_bear"
                score = -0.85
                confidence = min(0.6 + (curr_adx - 25) / 50.0, 0.95)
            else:
                regime = "trending"
                score = 0.3 if curr_close > curr_sma_mid else -0.3
                confidence = 0.55
        elif curr_adx < 20:
            regime = "ranging"
            score = 0.0
            confidence = 0.7
        else:
            regime = "transitional"
            score = 0.1 if is_bullish else (-0.1 if is_bearish else 0.0)
            confidence = 0.45

        # Simple trend fallback when ADX is weak but structure is clear
        if regime in ("sideways", "transitional", "ranging") and n >= 60:
            if is_bullish and curr_close > curr_sma_fast:
                regime = "trending_bull"
                score = 0.55
                confidence = 0.55
            elif is_bearish and curr_close < curr_sma_fast:
                regime = "trending_bear"
                score = -0.55
                confidence = 0.55

        if is_high_vol:
            if regime in ("trending_bear", "transitional") or score < 0:
                regime = "risk_off"
                score = -1.0
                confidence = 0.9
            else:
                regime = f"{regime}_high_vol"
                confidence = max(confidence - 0.15, 0.3)

        ratio = (curr_atr / atr_avg) if atr_avg > 0 else 0.0
        reason = f"Regime={regime} | ADX={curr_adx:.1f} | ATR ratio={ratio:.2f} | bars={n}"

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": "HOLD",
            "score": float(score),
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "regime": regime,
                "adx": curr_adx,
                "sma_mid": curr_sma_mid,
                "sma_slow": curr_sma_slow,
                "atr": curr_atr,
                "high_volatility": is_high_vol,
                "bars": n,
            },
        }
