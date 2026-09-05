import pytest
from bot.backtest.robustness import RobustnessTester

def test_robustness_insufficient_evidence():
    tester = RobustnessTester()
    trades = [0.05] * 10 # Only 10 trades, needs 15
    res = tester.test_monte_carlo(trades)
    assert res["passed"] is False
    assert "INSUFFICIENT_EVIDENCE" in res["reason"]

def test_robustness_passed():
    tester = RobustnessTester()
    # 20 trades, very high win rate, good profit factor
    trades = [0.05] * 18 + [-0.01, -0.01]
    res = tester.test_monte_carlo(trades)
    assert res["passed"] is True
    assert res["profit_factor"] > 1.2
    assert res["prob_positive"] >= 0.95

def test_robustness_failed_profit_factor():
    tester = RobustnessTester()
    # 20 trades, positive expectation but terrible profit factor (e.g. lots of tiny wins, one huge loss)
    # Actually let's just make it barely positive but huge gross loss
    trades = [0.01] * 10 + [-0.09] * 10
    # Wait, that's negative expectation. Let's make it slightly positive expectation, but profit factor < 1.2
    trades = [0.011] * 10 + [-0.01] * 10
    res = tester.test_monte_carlo(trades)

    assert res["passed"] is False
    assert res["profit_factor"] < 1.2
