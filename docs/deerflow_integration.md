# DeerFlow Integration Architecture

This repository is designed with a **DeerFlow-ready architecture**.
It provides the necessary hooks, boundaries, and CI/CD workflows to allow an external orchestrator like DeerFlow to interact with it, but **it does not contain DeerFlow itself**.

## Current Status
- **DeerFlow Ready:** Yes.
- **DeerFlow Integrated:** No. The actual DeerFlow engine is external.
- **Automated Research:** `EvolutionEngine` acts as a lightweight, internal AI hypothesis generator for testing the CI/CD pipeline hook, but does not represent full DeerFlow capabilities.

## Architecture

```text
DeerFlow (External System)
    |
    v (Triggers GitHub Action)
Research task (.github/workflows/research-pipeline.yml)
    |
    v
Cryptobot research APIs/scripts (bot.research.evolution)
    |
    v
Backtest/validation (WalkForwardValidator)
    |
    v
Structured research result (Markdown + JSON)
    |
    v (Uses peter-evans/create-pull-request)
GitHub PR -> Human Approval -> Paper Trading
```

## Security & Credentials
- DeerFlow **must NOT** receive Alpaca trading credentials.
- DeerFlow **must NOT** have direct push access to `main`. It may only open Pull Requests.
- The Cryptobot trading engine remains completely independent and does not require DeerFlow to execute trades.
