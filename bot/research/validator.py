import pandas as pd
from bot.backtest.engine import BacktestEngine
from bot.backtest.robustness import RobustnessTester

class WalkForwardValidator:
    def __init__(self, train_ratio=0.7):
        self.train_ratio = train_ratio

    def validate(self, agent, symbol: str, data: pd.DataFrame, benchmark: pd.DataFrame = None):
        """
        Splits data into TRAIN and VALIDATE periods.
        Runs backtest on both.
        Runs robustness checks on validation trades.
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

        # Robustness Testing
        robust_tester = RobustnessTester()
        robustness_report = robust_tester.test_monte_carlo(val_metrics.get("trades_list", []))

        # We can drop the trades list from the final report to avoid bloat
        train_metrics.pop("trades_list", None)
        val_metrics.pop("trades_list", None)

        # Validation checks to prevent overfitting
        passed = False
        status = "REJECTED"

        # Out-of-sample rule: Positive return, reasonable win rate, no catastrophic drawdown, passes robustness
        if robustness_report.get("reason", "").startswith("INSUFFICIENT_EVIDENCE"):
            status = "INSUFFICIENT_EVIDENCE"
            passed = False
        elif (val_metrics["total_return"] > 0.0 and
            val_metrics["max_drawdown"] > -0.25 and
            val_metrics["num_trades"] >= 15 and
            robustness_report["passed"]):
            passed = True
            status = "PASSED"

        report = {
            "agent": agent.name,
            "version": getattr(agent, "version", "1.0"),
            "symbol": symbol,
            "passed": passed,
            "status": status,
            "train": train_metrics,
            "validate": val_metrics,
            "robustness": robustness_report
        }

        return report
