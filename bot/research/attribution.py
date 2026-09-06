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

    def get_strategy_metrics(self, strategy_name: str) -> dict:
        returns = self.strategy_returns.get(strategy_name, [])
        metrics = {
            "trade_count": len(returns),
            "win_rate": 0.0,
            "expectancy": 0.0,
            "sharpe_proxy": 0.0,
            "sortino_proxy": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_proxy": 0.0
        }
        if not returns:
            return metrics

        returns_arr = np.array(returns)
        wins = returns_arr[returns_arr > 0]
        losses = returns_arr[returns_arr < 0]

        metrics["win_rate"] = len(wins) / len(returns) if returns else 0.0
        metrics["expectancy"] = np.mean(returns_arr)

        if np.std(returns_arr) > 0:
            metrics["sharpe_proxy"] = np.mean(returns_arr) / np.std(returns_arr)

        if len(losses) > 0 and np.std(losses) > 0:
            metrics["sortino_proxy"] = np.mean(returns_arr) / np.std(losses)

        gross_profit = np.sum(wins) if len(wins) > 0 else 0.0
        gross_loss = np.abs(np.sum(losses)) if len(losses) > 0 else 0.0
        if gross_loss > 0:
             metrics["profit_factor"] = gross_profit / gross_loss
        elif gross_profit > 0:
             metrics["profit_factor"] = 999.0

        cum_ret = np.cumprod(1 + returns_arr)
        running_max = np.maximum.accumulate(cum_ret)
        if len(running_max) > 0 and np.any(running_max > 0):
             drawdowns = (cum_ret - running_max) / running_max
             metrics["max_drawdown_proxy"] = np.min(drawdowns)

        return metrics

    def get_strategy_weight(self, strategy_name: str) -> float:
        returns = self.strategy_returns.get(strategy_name, [])
        if len(returns) < 15:
            return self.base_weight # Require 15 trades minimum to adapt weight

        metrics = self.get_strategy_metrics(strategy_name)
        sharpe = metrics["sharpe_proxy"]

        # Dampen extreme weights
        weight = self.base_weight * (1.0 + max(min(sharpe, 1.0), -0.5))
        return max(weight, 0.1) # Floor at 0.1
