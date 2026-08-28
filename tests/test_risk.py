import pytest
from bot.risk import calculate_position_size

def test_calculate_position_size_normal():
    # equity = 10000, risk = 0.01 (100)
    # atr = 2, stop_multiple = 2 -> risk_per_share = 4
    # shares = 100 / 4 = 25
    assert calculate_position_size(10000.0, 2.0, 0.01, 2.0) == 25

def test_calculate_position_size_rounding():
    # equity = 10000, risk = 0.01 (100)
    # atr = 3, stop_multiple = 2 -> risk_per_share = 6
    # shares = 100 / 6 = 16.666 -> 16
    assert calculate_position_size(10000.0, 3.0, 0.01, 2.0) == 16

def test_calculate_position_size_zero_atr():
    assert calculate_position_size(10000.0, 0.0, 0.01, 2.0) == 0

def test_calculate_position_size_negative_atr():
    assert calculate_position_size(10000.0, -1.0, 0.01, 2.0) == 0

def test_calculate_position_size_zero_equity():
    assert calculate_position_size(0.0, 2.0, 0.01, 2.0) == 0

def test_calculate_position_size_zero_risk():
    assert calculate_position_size(10000.0, 2.0, 0.0, 2.0) == 0
