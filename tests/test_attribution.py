import pytest
from bot.consensus import ConsensusEngine

def test_primary_agent_attribution():
    engine = ConsensusEngine(min_confidence=0.4)
    # Give TrendAgent a weight of 1.15 in config, Momentum is 0.95
    quant_signals = [
        {"agent": "TrendAgent", "signal": "BUY", "score": 0.8, "confidence": 0.8, "reason": ""},
        {"agent": "MomentumAgent", "signal": "BUY", "score": 0.9, "confidence": 0.9, "reason": ""}
    ]
    regime = {"features": {"regime": "sideways"}}

    res = engine.aggregate_signals("AAPL", quant_signals, regime, None)

    # 0.8 * 1.15 = 0.92
    # 0.9 * 0.95 = 0.855
    # So TrendAgent should be the primary agent
    assert res["primary_agent"] == "TrendAgent"
