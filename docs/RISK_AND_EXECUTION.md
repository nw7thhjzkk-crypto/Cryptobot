# Risk and Execution

Risk management is the ultimate authority in Cryptobot.

## Risk Engine
The `RiskEngine` enforces:
- Maximum position sizing (ATR-based).
- Maximum portfolio and symbol exposure.
- Drawdown breaker protection (halting entries if equity drops significantly).
- Prevention of duplicate orders or uncontrolled grids.

## Portfolio Engine
The `PortfolioEngine` manages portfolio-level logic, checking current positions and correlation limits before approving new signals.

## Execution Engine
The `ExecutionEngine` securely submits orders to the broker (Alpaca) in `PAPER_MODE` only. AI agents are strictly forbidden from directly interfacing with the execution layer.
