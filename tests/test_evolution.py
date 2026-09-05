import pytest
import pandas as pd
from bot.research.evolution import EvolutionEngine

def test_evolution_engine_hypothesis_mock():
    # Since we are mocking Gemini for tests via dummy key, it returns deterministic dict
    engine = EvolutionEngine()
    engine.is_configured = False # Force mock

    desc = "Test strategy"
    perf = {"train": {"total_return": 0.1}, "validate": {"total_return": -0.05}}

    hyp = engine.generate_hypothesis(desc, perf)

    assert hyp is not None
    assert "proposed_parameters" in hyp
    assert "entry_lookback" in hyp["proposed_parameters"]
