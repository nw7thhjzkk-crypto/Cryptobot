import pytest
from bot.risk import (
    calculate_position_size,
    calculate_stop_price,
    check_portfolio_risk,
    check_drawdown_breaker
)

class TestCalculatePositionSize:
    def test_normal_case(self):
        # equity = 10000, atr = 5, risk = 0.01 (100 risk amount)
        # risk_per_share = 5 * 2.0 = 10
        # shares = 100 / 10 = 10
        shares = calculate_position_size(
            account_equity=10000.0,
            atr=5.0,
            risk_per_trade_pct=0.01,
            stop_multiple=2.0
        )
        assert shares == 10

    def test_atr_zero(self):
        shares = calculate_position_size(
            account_equity=10000.0,
            atr=0.0,
            risk_per_trade_pct=0.01
        )
        assert shares == 0

    def test_atr_negative(self):
        shares = calculate_position_size(
            account_equity=10000.0,
            atr=-1.0,
            risk_per_trade_pct=0.01
        )
        assert shares == 0

    def test_rounding_down(self):
        # equity = 10000, atr = 3, risk = 0.01 (100 risk amount)
        # risk_per_share = 3 * 2.0 = 6
        # shares = 100 / 6 = 16.666... -> 16
        shares = calculate_position_size(
            account_equity=10000.0,
            atr=3.0,
            risk_per_trade_pct=0.01,
            stop_multiple=2.0
        )
        assert shares == 16


class TestCalculateStopPrice:
    def test_buy_side(self):
        # entry = 100, atr = 2, mult = 2 -> stop = 100 - 4 = 96
        stop = calculate_stop_price(
            entry_price=100.0,
            atr=2.0,
            side='buy',
            stop_multiple=2.0
        )
        assert stop == 96.0

    def test_sell_side(self):
        # entry = 100, atr = 2, mult = 2 -> stop = 100 + 4 = 104
        stop = calculate_stop_price(
            entry_price=100.0,
            atr=2.0,
            side='sell',
            stop_multiple=2.0
        )
        assert stop == 104.0

    def test_case_insensitivity(self):
        stop = calculate_stop_price(
            entry_price=100.0,
            atr=2.0,
            side='BUY',
            stop_multiple=2.0
        )
        assert stop == 96.0

    def test_custom_multiple(self):
        stop = calculate_stop_price(
            entry_price=100.0,
            atr=2.0,
            side='buy',
            stop_multiple=3.0
        )
        assert stop == 94.0


class TestCheckPortfolioRisk:
    def test_risk_allowed(self):
        # open risk = 50 (from -50 unrl_pl)
        # new risk = 100
        # total = 150
        # max allowed = 10000 * 0.02 = 200
        # 150 <= 200 -> True
        open_positions = [{'unrealized_pl': -50.0}, {'unrealized_pl': 10.0}]
        allowed = check_portfolio_risk(
            open_positions=open_positions,
            new_position_risk=100.0,
            max_total_risk_pct=0.02,
            account_equity=10000.0
        )
        assert allowed is True

    def test_risk_exceeded(self):
        # open risk = 150 (from -150 unrl_pl)
        # new risk = 100
        # total = 250
        # max allowed = 10000 * 0.02 = 200
        # 250 <= 200 -> False
        open_positions = [{'unrealized_pl': -150.0}]
        allowed = check_portfolio_risk(
            open_positions=open_positions,
            new_position_risk=100.0,
            max_total_risk_pct=0.02,
            account_equity=10000.0
        )
        assert allowed is False

    def test_empty_positions(self):
        # new risk = 100, allowed = 200 -> True
        allowed = check_portfolio_risk(
            open_positions=[],
            new_position_risk=100.0,
            max_total_risk_pct=0.02,
            account_equity=10000.0
        )
        assert allowed is True

    def test_only_profitable_positions(self):
        # open risk = 0, new risk = 100, allowed = 200 -> True
        open_positions = [{'unrealized_pl': 50.0}, {'unrealized_pl': 100.0}]
        allowed = check_portfolio_risk(
            open_positions=open_positions,
            new_position_risk=100.0,
            max_total_risk_pct=0.02,
            account_equity=10000.0
        )
        assert allowed is True


class TestCheckDrawdownBreaker:
    def test_empty_history(self):
        breached = check_drawdown_breaker(
            equity_history=[],
            max_drawdown_pct=0.1
        )
        assert breached is False

    def test_no_drawdown(self):
        history = [10000, 10100, 10200]
        breached = check_drawdown_breaker(
            equity_history=history,
            max_drawdown_pct=0.1
        )
        assert breached is False

    def test_drawdown_below_threshold(self):
        # peak = 10000, current = 9500
        # drawdown = 0.05
        # threshold = 0.1
        history = [9000, 10000, 9500]
        breached = check_drawdown_breaker(
            equity_history=history,
            max_drawdown_pct=0.1
        )
        assert breached is False

    def test_drawdown_exceeds_threshold(self):
        # peak = 10000, current = 8500
        # drawdown = 0.15
        # threshold = 0.1
        history = [9000, 10000, 8500]
        breached = check_drawdown_breaker(
            equity_history=history,
            max_drawdown_pct=0.1
        )
        assert breached is True

    def test_windowing(self):
        # Peak of 10000 is outside window.
        # Inside window: peak is 9000, current is 8500.
        # Drawdown = 500/9000 = 0.055
        # Threshold = 0.1
        # Should be False, because the 10000 peak is ignored.
        history = [10000, 9000, 8500]
        breached = check_drawdown_breaker(
            equity_history=history,
            max_drawdown_pct=0.1,
            window_days=2
        )
        assert breached is False

    def test_zero_peak(self):
        history = [0, 0, 0]
        breached = check_drawdown_breaker(
            equity_history=history,
            max_drawdown_pct=0.1
        )
        assert breached is False
