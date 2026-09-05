import pytest
from bot.consensus import ConsensusEngine
from bot.research.attribution import AttributionTracker

def test_primary_agent_attribution():
    tracker = AttributionTracker()
    # Mock the weights directly so TrendAgent has a higher weight than Momentum
    tracker.get_strategy_weight = lambda name: 1.5 if name == "TrendAgent" else 0.5

    engine = ConsensusEngine(attribution_tracker=tracker)

    quant_signals = [
        {"agent": "TrendAgent", "signal": "BUY", "score": 0.8, "confidence": 0.8, "reason": ""},
        {"agent": "MomentumAgent", "signal": "BUY", "score": 0.9, "confidence": 0.9, "reason": ""}
    ]
    regime = {"features": {"regime": "sideways"}}

    res = engine.aggregate_signals("AAPL", quant_signals, regime, None)

    # TrendAgent: 0.8 * 1.5 * 0.8 = 0.96 (score * perf_mult * confidence)
    # Momentum: 0.9 * 0.5 * 0.9 = 0.405
    assert res["primary_agent"] == "TrendAgent"
