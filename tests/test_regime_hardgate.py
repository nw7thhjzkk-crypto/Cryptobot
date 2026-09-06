import pytest
import pandas as pd
import numpy as np
from bot.regime_engine import MarketRegimeEngine
from bot.consensus import ConsensusEngine

def test_regime_hard_gate_nan_values():
    df = pd.DataFrame({"open": [10.0]*100, "high": [11.0]*100, "low": [9.0]*100, "close": [10.0]*100, "volume": [1000]*100})
    engine = MarketRegimeEngine()
    import bot.regime_engine
    def mock_calc_atr(df, length=14):
        s = pd.Series([1.0]*100)
        s.iloc[-1] = np.nan
        return s
    original = bot.regime_engine.calculate_atr
    bot.regime_engine.calculate_atr = mock_calc_atr
    try:
        result = engine.analyze("TEST", df)
        assert result["regime"] == "unknown"
        assert "NaN" in result["reason"]
    finally:
        bot.regime_engine.calculate_atr = original

def test_consensus_hard_gate_blocks_signal():
    engine = ConsensusEngine()
    regime_signal = {"regime": "ranging", "confidence": 0.9}
    quant_signals = [{
        "agent": "TrendAgent",
        "signal": "BUY",
        "score": 0.8,
        "confidence": 0.9,
        "regime_compatibility": ["trending_bull", "trending_bear"]
    }]
    result = engine.aggregate_signals("TEST", quant_signals, regime_signal)
    assert result["signal"] == "HOLD"
    assert result["score"] == 0.0
