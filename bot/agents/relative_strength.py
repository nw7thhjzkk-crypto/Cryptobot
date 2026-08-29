import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent

class RelativeStrengthAgent(BaseAgent):
    def __init__(self):
        super().__init__("RelativeStrengthAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, benchmark_history: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
        if benchmark_history is None or benchmark_history.empty:
            return self._create_hold_signal(symbol, "No benchmark data provided for relative strength")

        lookback = 20
        if len(price_history) < lookback or len(benchmark_history) < lookback:
             return self._create_hold_signal(symbol, "Insufficient data for relative strength analysis")

        df = price_history.copy()
        bench_df = benchmark_history.copy()

        df['date'] = df.index
        bench_df['date'] = bench_df.index
        merged = pd.merge(df, bench_df, on='date', suffixes=('_sym', '_bench'))

        if len(merged) < lookback:
            return self._create_hold_signal(symbol, "Insufficient aligned data")

        rs_ratio = merged['close_sym'] / merged['close_bench']

        rs_roc = (rs_ratio.iloc[-1] - rs_ratio.iloc[-lookback]) / rs_ratio.iloc[-lookback] * 100

        signal = "HOLD"
        confidence = 0.0
        reason = "Neutral relative strength"

        if rs_roc > 2.0:
            signal = "BUY"
            confidence = min(0.5 + (rs_roc - 2.0) * 0.1, 0.85)
            reason = f"Outperforming benchmark by {rs_roc:.2f}% over {lookback} periods"
        elif rs_roc < -2.0:
            signal = "SELL"
            confidence = min(0.5 + (abs(rs_roc) - 2.0) * 0.1, 0.85)
            reason = f"Underperforming benchmark by {abs(rs_roc):.2f}% over {lookback} periods"

        score = confidence if signal == "BUY" else (-confidence if signal == "SELL" else 0.0)

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "reason": reason,
            "features": {
                "rs_roc_20": float(rs_roc)
            }
        }
