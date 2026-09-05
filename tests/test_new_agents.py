import pytest
import pandas as pd
from bot.agents.donchian import DonchianBreakoutAgent
from bot.agents.dual_momentum import DualMomentumAgent
from bot.agents.range_expansion import RangeExpansionAgent

def test_donchian_breakout():
    prices = list(range(100, 150))
    df = pd.DataFrame({
        'close': prices,
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'volume': [1000] * 50
    })

    agent = DonchianBreakoutAgent(entry_lookback=20, exit_lookback=10)
    res = agent.analyze("AAPL", df)

    # In a rising 1,2,3,4 trend, close of today is 149, previous high was 149 (for p=148).
    # Since curr_close (149) is NOT > dh_val (149), it doesn't trigger BUY with strictly >
    # We should make the test have an actual breakout

    prices = [100.0] * 50 + [120.0]
    df2 = pd.DataFrame({
        'close': prices,
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'volume': [1000] * 51
    })
    res2 = agent.analyze("AAPL", df2)
    assert res2["signal"] == "BUY"

def test_range_expansion():
    prices = [100.0] * 50
    df = pd.DataFrame({
        'close': prices + [105.0],
        'open': prices + [100.0],
        'high': [p + 1 for p in prices] + [106.0],
        'low': [p - 1 for p in prices] + [99.0],
        'volume': [1000] * 51
    })

    agent = RangeExpansionAgent()
    res = agent.analyze("AAPL", df)

    assert res["signal"] == "BUY"
    assert res["confidence"] > 0.5
