import numpy as np

class RobustnessTester:
    def __init__(self, num_simulations=1000):
        self.num_simulations = num_simulations

    def test_monte_carlo(self, trades):
        """
        Resamples trade returns to see if the strategy is robust to trade order and outliers.
        """
        if not trades or len(trades) < 5:
            return {"passed": False, "reason": "Insufficient trades for monte carlo", "prob_positive": 0.0, "mean_simulated_return": 0.0}

        returns = np.array(trades)

        simulated_returns = []
        for _ in range(self.num_simulations):
            # Bootstrap resampling with replacement
            simulated = np.random.choice(returns, size=len(returns), replace=True)
            # Cumulative compound return
            comp_ret = np.prod(1 + simulated) - 1
            simulated_returns.append(comp_ret)

        simulated_returns = np.array(simulated_returns)
        # Calculate the probability that total return is > 0
        prob_positive = np.sum(simulated_returns > 0) / len(simulated_returns)
        mean_sim = float(np.mean(simulated_returns))

        # Require 90% of randomized trade paths to be profitable
        passed = prob_positive >= 0.90

        return {
            "passed": bool(passed),
            "prob_positive": float(prob_positive),
            "mean_simulated_return": mean_sim
        }
