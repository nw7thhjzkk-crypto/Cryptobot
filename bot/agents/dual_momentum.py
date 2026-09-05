import pandas as pd
from typing import Dict, Any
from bot.agents.base import BaseAgent

class DualMomentumAgent(BaseAgent):
    def __init__(self, fast_period: int = 5, mid_period: int = 20, slow_period: int = 60):
        super().__init__("DualMomentumAgent")
        self.fast = fast_period
        self.mid = mid_period
        self.slow = slow_period

    def analyze(self, symbol: str, price_history: pd.DataFrame, benchmark_history: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
        if len(price_history) < self.slow + 5:
             return self._create_hold_signal(symbol, "Insufficient data for dual momentum analysis")

        if benchmark_history is None or benchmark_history.empty:
             return self._create_hold_signal(symbol, "Missing benchmark history")

        df = price_history.copy()
        bench_df = benchmark_history.copy()

        df['date'] = df.index
        bench_df['date'] = bench_df.index
        merged = pd.merge(df, bench_df, on='date', suffixes=('_sym', '_bench'))

        if len(merged) < self.slow + 1:
            return self._create_hold_signal(symbol, "Insufficient aligned data for dual momentum")

        # Absolute Momentum for symbol
        roc_fast = (merged['close_sym'].iloc[-1] - merged['close_sym'].iloc[-self.fast]) / merged['close_sym'].iloc[-self.fast] * 100
        roc_mid = (merged['close_sym'].iloc[-1] - merged['close_sym'].iloc[-self.mid]) / merged['close_sym'].iloc[-self.mid] * 100
        roc_slow = (merged['close_sym'].iloc[-1] - merged['close_sym'].iloc[-self.slow]) / merged['close_sym'].iloc[-self.slow] * 100

        # Absolute Momentum for benchmark
        bench_roc_fast = (merged['close_bench'].iloc[-1] - merged['close_bench'].iloc[-self.fast]) / merged['close_bench'].iloc[-self.fast] * 100
        bench_roc_mid = (merged['close_bench'].iloc[-1] - merged['close_bench'].iloc[-self.mid]) / merged['close_bench'].iloc[-self.mid] * 100
        bench_roc_slow = (merged['close_bench'].iloc[-1] - merged['close_bench'].iloc[-self.slow]) / merged['close_bench'].iloc[-self.slow] * 100

        # Relative Momentum (Symbol vs Benchmark)
        rel_fast = roc_fast - bench_roc_fast
        rel_mid = roc_mid - bench_roc_mid
        rel_slow = roc_slow - bench_roc_slow

        # Scoring
        score_val = 0.0
        # Give higher weight to mid and slow trends for stability
        if rel_slow > 0 and roc_slow > 0: score_val += 0.4
        elif rel_slow < 0 and roc_slow < 0: score_val -= 0.4

        if rel_mid > 0 and roc_mid > 0: score_val += 0.35
        elif rel_mid < 0 and roc_mid < 0: score_val -= 0.35

        if rel_fast > 0 and roc_fast > 0: score_val += 0.25
        elif rel_fast < 0 and roc_fast < 0: score_val -= 0.25

        signal = "HOLD"
        confidence = 0.0
        reason = "Mixed or weak momentum"

        if score_val >= 0.5:
            signal = "BUY"
            confidence = min(score_val, 0.95)
            reason = f"Strong dual momentum (Rel ROC: {self.slow}d={rel_slow:.1f}%, {self.mid}d={rel_mid:.1f}%, {self.fast}d={rel_fast:.1f}%)"
        elif score_val <= -0.5:
            signal = "SELL"
            confidence = min(abs(score_val), 0.95)
            reason = f"Weak dual momentum (Rel ROC: {self.slow}d={rel_slow:.1f}%, {self.mid}d={rel_mid:.1f}%, {self.fast}d={rel_fast:.1f}%)"

        return {
            "agent": self.name,
            "symbol": symbol,
            "signal": signal,
            "score": float(score_val),
            "confidence": float(confidence),
            "reason": reason,
            "features": {
                "roc_fast": float(roc_fast),
                "roc_mid": float(roc_mid),
                "roc_slow": float(roc_slow),
                "rel_fast": float(rel_fast),
                "rel_mid": float(rel_mid),
                "rel_slow": float(rel_slow),
            }
        }
