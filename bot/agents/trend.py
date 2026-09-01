import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent
from bot.strategy import calculate_macd, calculate_adx, calculate_atr

class TrendAgent(BaseAgent):
    def __init__(self):
        super().__init__("TrendAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < 60:
            return self._create_hold_signal(symbol, "Insufficient data for trend analysis")

        df = price_history.copy()
        ema20 = df['close'].ewm(span=20, adjust=False).mean()
        ema50 = df['close'].ewm(span=50, adjust=False).mean()
        macd_hist = calculate_macd(df)
        adx = calculate_adx(df, length=14)
        atr = calculate_atr(df, length=14)

        if ema20.empty or ema50.empty or macd_hist.empty or adx.empty:
            return self._create_hold_signal(symbol, "Failed to calculate indicators")

        prev_ema20, curr_ema20 = float(ema20.iloc[-2]), float(ema20.iloc[-1])
        prev_ema50, curr_ema50 = float(ema50.iloc[-2]), float(ema50.iloc[-1])
        curr_macd_hist = float(macd_hist.iloc[-1])
        curr_adx = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0.0
        curr_close = float(df['close'].iloc[-1])

        # Volume confirmation
        vol_avg = df['volume'].rolling(window=20).mean().iloc[-1] if 'volume' in df.columns else 1.0
        curr_vol = float(df['volume'].iloc[-1]) if 'volume' in df.columns else 1.0
        rel_vol = curr_vol / vol_avg if vol_avg > 0 else 1.0

        cross_above = prev_ema20 <= prev_ema50 and curr_ema20 > curr_ema50
        cross_below = prev_ema20 >= prev_ema50 and curr_ema20 < curr_ema50

        dist_pct = (curr_ema20 - curr_ema50) / curr_ema50 if curr_ema50 != 0 else 0.0

        signal = "HOLD"
        confidence = 0.0
        reason = "No clear trend signal"

        # Only trade strong trends (ADX filter - key improvement)
        if curr_adx < 22:
            return self._create_hold_signal(
                symbol,
                f"ADX too low ({curr_adx:.1f}) - not a strong trend",
                features={"adx": curr_adx, "ema20": curr_ema20, "ema50": curr_ema50}
            )

        if curr_ema20 > curr_ema50 and curr_macd_hist > 0:
            signal = "BUY"
            confidence = min(0.45 + abs(dist_pct) * 8 + (curr_adx - 22) / 40.0, 0.95)
            reason = f"EMA20 > EMA50 + positive MACD | ADX={curr_adx:.1f}"
            if cross_above:
                confidence = min(confidence + 0.25, 0.98)
                reason = f"Bullish EMA crossover confirmed by MACD | ADX={curr_adx:.1f}"
            if rel_vol > 1.3:
                confidence = min(confidence + 0.1, 0.98)
                reason += " + volume confirmation"

        elif curr_ema20 < curr_ema50 and curr_macd_hist < 0:
            signal = "SELL"
            confidence = min(0.45 + abs(dist_pct) * 8 + (curr_adx - 22) / 40.0, 0.95)
            reason = f"EMA20 < EMA50 + negative MACD | ADX={curr_adx:.1f}"
            if cross_below:
                confidence = min(confidence + 0.25, 0.98)
                reason = f"Bearish EMA crossover confirmed by MACD | ADX={curr_adx:.1f}"
            if rel_vol > 1.3:
                confidence = min(confidence + 0.1, 0.98)
                reason += " + volume confirmation"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": float(score),
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "ema20": curr_ema20,
                "ema50": curr_ema50,
                "macd_hist": curr_macd_hist,
                "adx": curr_adx,
                "rel_vol": float(rel_vol)
            }
        }
