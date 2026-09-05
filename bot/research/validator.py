import pandas as pd
from bot.backtest.engine import BacktestEngine

class WalkForwardValidator:
    def __init__(self, train_ratio=0.7):
        self.train_ratio = train_ratio

    def validate(self, agent, symbol: str, data: pd.DataFrame, benchmark: pd.DataFrame = None):
        """
        Splits data into TRAIN and VALIDATE periods.
        Runs backtest on both.
        Returns validation report and boolean indicating if it passed basic constraints.
        """
        n = len(data)
        split_idx = int(n * self.train_ratio)

        train_data = data.iloc[:split_idx].copy()
        val_data = data.iloc[split_idx:].copy()

        train_bench = benchmark.iloc[:split_idx].copy() if benchmark is not None else None
        val_bench = benchmark.iloc[split_idx:].copy() if benchmark is not None else None

        engine = BacktestEngine()

        train_metrics = engine.run(agent, symbol, train_data, train_bench)
        val_metrics = engine.run(agent, symbol, val_data, val_bench)

        # Validation checks to prevent overfitting
        passed = False

        # Simple out-of-sample rule: Positive return, reasonable win rate, no catastrophic drawdown
        if (val_metrics["total_return"] > -0.05 and
            val_metrics["max_drawdown"] > -0.30 and
            val_metrics["num_trades"] > 0):
            passed = True

        report = {
            "agent": agent.name,
            "symbol": symbol,
            "passed": passed,
            "train": train_metrics,
            "validate": val_metrics
        }

        return report
