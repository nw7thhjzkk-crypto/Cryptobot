import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_capital=10000.0, transaction_cost=0.001):
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost

    def run(self, agent, symbol: str, data: pd.DataFrame, benchmark: pd.DataFrame = None):
        """
        Runs a deterministic, single-asset backtest for a given agent on a DataFrame.
        """
        if len(data) == 0:
            return self._empty_result()

        capital = self.initial_capital
        position = 0
        entry_price = 0.0

        trades = []
        equity_curve = []

        # We need to simulate stepping through time to prevent lookahead bias.
        # This is slow, but correct. For production research, vectorized might be preferred,
        # but this is deterministic and uses the exact agent logic.

        # Start at a minimum index so indicators can warm up
        warmup = 65
        if len(data) <= warmup:
            return self._empty_result()

        for i in range(warmup, len(data)):
            # Create a slice of data up to current bar to pass to agent
            # Use i+1 because iloc upper bound is exclusive
            current_slice = data.iloc[:i+1].copy()
            current_close = float(current_slice['close'].iloc[-1])

            # Record daily equity
            if position > 0:
                current_value = position * current_close
                equity_curve.append(capital + current_value)
            else:
                equity_curve.append(capital)

            # Check if agent requires benchmark
            kwargs = {}
            if benchmark is not None:
                kwargs['benchmark_history'] = benchmark.iloc[:i+1].copy()

            # Get signal
            res = agent.analyze(symbol, current_slice, **kwargs)
            signal = res.get("signal", "HOLD")

            # Extremely simple execution: enter on next open (we just use close here for simplicity in this basic framework)
            # In a full system, you would execute on next open to avoid lookahead.

            if signal == "BUY" and position == 0:
                # Calculate qty we can afford
                trade_size = capital * 0.95 # Leave some cash
                qty = trade_size / current_close
                cost = trade_size * self.transaction_cost

                position = qty
                entry_price = current_close
                capital -= (trade_size + cost)

            elif signal == "SELL" and position > 0:
                proceeds = position * current_close
                cost = proceeds * self.transaction_cost

                capital += (proceeds - cost)

                # Record trade
                pnl = (current_close - entry_price) / entry_price
                trades.append(pnl)

                position = 0
                entry_price = 0.0

        # Close open position at end
        if position > 0:
            proceeds = position * float(data['close'].iloc[-1])
            cost = proceeds * self.transaction_cost
            capital += (proceeds - cost)
            pnl = (float(data['close'].iloc[-1]) - entry_price) / entry_price
            trades.append(pnl)
            equity_curve.append(capital)

        return self._calculate_metrics(trades, equity_curve)

    def _empty_result(self):
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "num_trades": 0
        }

    def _calculate_metrics(self, trades, equity_curve):
        if not trades or len(equity_curve) < 2:
            return self._empty_result()

        total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital

        eq_series = pd.Series(equity_curve)
        daily_returns = eq_series.pct_change().dropna()

        # Approx Sharpe (Assuming 252 trading days)
        if daily_returns.std() == 0:
            sharpe = 0.0
        else:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

        rolling_max = eq_series.cummax()
        drawdowns = (eq_series - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()

        wins = sum(1 for t in trades if t > 0)
        win_rate = wins / len(trades)

        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "num_trades": len(trades)
        }
