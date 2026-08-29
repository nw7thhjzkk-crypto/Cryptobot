import pytest
from bot.consensus import ConsensusEngine

def test_consensus_engine_unanimous_buy():
    engine = ConsensusEngine(min_confidence=0.4)
    quant_signals = [
        {"agent": "TrendAgent", "signal": "BUY", "score": 0.8, "confidence": 0.8, "reason": ""},
        {"agent": "MomentumAgent", "signal": "BUY", "score": 0.6, "confidence": 0.6, "reason": ""}
    ]
    regime = {"features": {"regime": "bullish"}}

    res = engine.aggregate_signals("AAPL", quant_signals, regime, None)

    assert res["symbol"] == "AAPL"
    assert res["signal"] == "BUY"
    assert res["confidence"] >= 0.4

def test_consensus_engine_risk_off_override():
    engine = ConsensusEngine(min_confidence=0.4)
    quant_signals = [
        {"agent": "TrendAgent", "signal": "BUY", "score": 0.9, "confidence": 0.9, "reason": ""},
    ]
    regime = {"features": {"regime": "risk-off"}}

    res = engine.aggregate_signals("AAPL", quant_signals, regime, None)
    assert res["signal"] == "HOLD"

def test_consensus_engine_gemini_veto():
    engine = ConsensusEngine(min_confidence=0.4)
    quant_signals = [
        {"agent": "TrendAgent", "signal": "BUY", "score": 0.9, "confidence": 0.9, "reason": ""},
    ]
    regime = {"features": {"regime": "sideways"}}
    gemini_signal = {"agent": "GeminiContextAgent", "signal": "SELL", "score": -0.8, "confidence": 0.8, "reason": "Bad news"}

    res = engine.aggregate_signals("AAPL", quant_signals, regime, gemini_signal)

    assert res["signal"] == "HOLD"
