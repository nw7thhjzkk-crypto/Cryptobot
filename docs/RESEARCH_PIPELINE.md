# Research Pipeline

Cryptobot features a thorough research and testing pipeline to validate new trading concepts out-of-sample before they reach paper trading.

## Backtesting Engine
The `BacktestEngine` performs a chronological walk-forward simulation that prevents lookahead bias and accounts for slippage and transaction costs.

## Walk-Forward Validation
The `WalkForwardValidator` splits historical data into Training and Validation periods. AI-generated or manually proposed strategies must show positive returns and pass constraints on the out-of-sample validation data.

## Robustness Testing
The `RobustnessTester` utilizes Monte Carlo resampling to simulate a large number of random trade sequences. Strategies must pass statistical significance thresholds (e.g., >95% probability of positive returns) to be eligible.

## AI Evolution Engine
The `EvolutionEngine` queries Gemini to generate parameter hypotheses for underperforming strategies, then rigorously backtests and validates the hypothesis in a secure sandbox.
