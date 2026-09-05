from collections import defaultdict
import numpy as np

class AttributionTracker:
    """Tracks performance and assigns dynamic weights to strategies."""
    def __init__(self, history_limit=100):
        self.strategy_returns = defaultdict(list)
        self.history_limit = history_limit
        self.base_weight = 1.0

    def log_trade(self, strategy_name: str, pnl: float):
        self.strategy_returns[strategy_name].append(pnl)
        if len(self.strategy_returns[strategy_name]) > self.history_limit:
            self.strategy_returns[strategy_name].pop(0)

    def get_strategy_weight(self, strategy_name: str) -> float:
        returns = self.strategy_returns.get(strategy_name, [])
        if len(returns) < 10:
            return self.base_weight # Not enough history, use default

        returns_arr = np.array(returns)
        mean_ret = np.mean(returns_arr)
        std_ret = np.std(returns_arr)

        if std_ret == 0:
            return self.base_weight

        # Basic proxy for Sharpe
        sharpe = mean_ret / std_ret

        # Dampen extreme weights
        weight = self.base_weight * (1.0 + max(min(sharpe, 1.0), -0.5))
        return max(weight, 0.1) # Floor at 0.1
