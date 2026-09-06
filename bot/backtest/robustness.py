import numpy as np

class RobustnessTester:
    def __init__(self, num_simulations=1000):
        self.num_simulations = num_simulations

    def test_monte_carlo(self, trades):
        """
        Resamples trade returns to see if the strategy is robust to trade order and outliers.
        """
        # Small sample protection
        if not trades or len(trades) < 15:
            return {
                "passed": False,
                "reason": "INSUFFICIENT_EVIDENCE: Need at least 15 trades for statistical significance.",
                "prob_positive": 0.0,
                "mean_simulated_return": 0.0,
                "profit_factor": 0.0
            }

        returns = np.array(trades)

        # Calculate Profit Factor
        gross_profit = np.sum(returns[returns > 0])
        gross_loss = np.abs(np.sum(returns[returns < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999.0

        simulated_returns = []
        for _ in range(self.num_simulations):
            # Bootstrap resampling with replacement
            simulated = np.random.choice(returns, size=len(returns), replace=True)
            simulated = simulated - 0.001
            # Cumulative compound return
            comp_ret = np.prod(1 + simulated) - 1
            simulated_returns.append(comp_ret)

        simulated_returns = np.array(simulated_returns)
        # Calculate the probability that total return is > 0
        prob_positive = np.sum(simulated_returns > 0) / len(simulated_returns)
        mean_sim = float(np.mean(simulated_returns))

        # Multidimensional robustness check:
        # 1. 95% of randomized trade paths must be profitable
        # 2. Profit factor must be > 1.2
        # 3. Minimum 15 trades (handled above)
        passed = prob_positive >= 0.95 and profit_factor > 1.2

        reason = "PASSED_ROBUSTNESS" if passed else "FAILED_ROBUSTNESS_METRICS"

        return {
            "passed": bool(passed),
            "reason": reason,
            "prob_positive": float(prob_positive),
            "mean_simulated_return": mean_sim,
            "profit_factor": float(profit_factor)
        }
