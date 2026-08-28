import unittest
from bot.risk import check_portfolio_risk

class TestRisk(unittest.TestCase):
    def test_check_portfolio_risk_no_positions_within_limits(self):
        # account equity = 1000, max risk = 0.05 (50), new risk = 40 => 40 <= 50 (True)
        result = check_portfolio_risk(
            open_positions=[],
            new_position_risk=40.0,
            max_total_risk_pct=0.05,
            account_equity=1000.0
        )
        self.assertTrue(result)

    def test_check_portfolio_risk_no_positions_exceeds_limits(self):
        # account equity = 1000, max risk = 0.05 (50), new risk = 60 => 60 <= 50 (False)
        result = check_portfolio_risk(
            open_positions=[],
            new_position_risk=60.0,
            max_total_risk_pct=0.05,
            account_equity=1000.0
        )
        self.assertFalse(result)

    def test_check_portfolio_risk_positive_unrealized_pl(self):
        # positive unrealized_pl should not add to risk
        open_positions = [{'unrealized_pl': 100.0}]
        # account equity = 1000, max risk = 0.05 (50), open risk = 0, new risk = 40 => 40 <= 50 (True)
        result = check_portfolio_risk(
            open_positions=open_positions,
            new_position_risk=40.0,
            max_total_risk_pct=0.05,
            account_equity=1000.0
        )
        self.assertTrue(result)

    def test_check_portfolio_risk_negative_unrealized_pl(self):
        # negative unrealized_pl should add absolute value to risk
        open_positions = [{'unrealized_pl': -20.0}]
        # account equity = 1000, max risk = 0.05 (50), open risk = 20, new risk = 40 => 60 <= 50 (False)
        result = check_portfolio_risk(
            open_positions=open_positions,
            new_position_risk=40.0,
            max_total_risk_pct=0.05,
            account_equity=1000.0
        )
        self.assertFalse(result)

    def test_check_portfolio_risk_boundary(self):
        # total combined risk exactly equals allowed risk
        open_positions = [{'unrealized_pl': -10.0}]
        # account equity = 1000, max risk = 0.05 (50), open risk = 10, new risk = 40 => 50 <= 50 (True)
        result = check_portfolio_risk(
            open_positions=open_positions,
            new_position_risk=40.0,
            max_total_risk_pct=0.05,
            account_equity=1000.0
        )
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
