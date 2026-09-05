# Platform Architecture

## Core Components
- **MarketRegimeEngine**: Determines the macro state of the market.
- **Quant Strategy Platform**: Modular trading strategies.
- **ConsensusEngine**: Aggregates signals and weights them dynamically.
- **PortfolioEngine**: Determines capital allocation based on volatility.
- **RiskEngine**: Implements hard constraints (max position, daily loss limits).
- **Broker**: Alpaca paper execution.
- **Research/Evolution**: Generates and validates new strategies via AI.
