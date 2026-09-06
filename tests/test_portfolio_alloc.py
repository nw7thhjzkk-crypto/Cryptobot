import pytest
from bot.portfolio import PortfolioEngine

def test_portfolio_inverse_vol():
    engine = PortfolioEngine(max_portfolio_exposure=0.9, max_positions=10, max_symbol_exposure=0.15, allocation_method="inverse_volatility")
    alloc1 = engine.calculate_allocation("TEST1", 10000.0, 1.0)
    alloc2 = engine.calculate_allocation("TEST2", 10000.0, 0.25)

    assert alloc1 == 450.0
    assert alloc2 == 1350.0

def test_portfolio_symbol_max_cap():
    engine = PortfolioEngine(max_portfolio_exposure=0.9, max_positions=2, max_symbol_exposure=0.2)
    alloc = engine.calculate_allocation("TEST", 10000.0)
    assert alloc == 2000.0
