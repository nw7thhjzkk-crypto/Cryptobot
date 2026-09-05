import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent

class VolumeAgent(BaseAgent):
    def __init__(self):
        super().__init__("VolumeAgent", version="1.1", parameters={"volume_sma_len": 20, "price_roc_len": 3}, regime_compatibility=["trending_bull", "trending_bear", "ranging"])

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        if len(price_history) < self.parameters["volume_sma_len"] + 5:
            return self._create_hold_signal(symbol, "Insufficient data for Volume Agent")

        df = price_history.copy()

        v_len = self.parameters["volume_sma_len"]
        p_len = self.parameters["price_roc_len"]

        avg_vol = df['volume'].iloc[-v_len-1:-1].mean()
        curr_vol = float(df['volume'].iloc[-1])

        if avg_vol == 0:
            return self._create_hold_signal(symbol, "Average volume is zero")

        vol_ratio = curr_vol / avg_vol

        price_roc = (df['close'].iloc[-1] - df['close'].iloc[-p_len-1]) / df['close'].iloc[-p_len-1] * 100

        signal = "HOLD"
        confidence = 0.0
        reason = "Normal volume activity"

        if vol_ratio > 2.0:
            if price_roc > 1.5:
                signal = "BUY"
                confidence = min(0.5 + (vol_ratio - 2.0) * 0.1, 0.90)
                reason = f"High volume price surge (Vol Ratio {vol_ratio:.1f}, ROC {price_roc:.1f}%)"
            elif price_roc < -1.5:
                signal = "SELL"
                confidence = min(0.5 + (vol_ratio - 2.0) * 0.1, 0.90)
                reason = f"High volume price drop (Vol Ratio {vol_ratio:.1f}, ROC {price_roc:.1f}%)"

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
                "vol_ratio": curr_vol / avg_vol if avg_vol > 0 else 0,
                "price_roc_3": price_roc
            }
        }
