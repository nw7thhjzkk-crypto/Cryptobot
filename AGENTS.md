# Cryptobot - AI Engineering Rules

This file outlines the guidelines for AI agents (like Jules) working on the Cryptobot repository.

## 1. Safety and Paper Trading First
* Cryptobot is strictly a PAPER TRADING platform. Never introduce live broker credentials, margin, leverage, or modifications that bypass the `PAPER_MODE` safety checks.
* AI agents MUST NOT directly execute trades. All trades must go through the deterministic `RiskEngine` and `ExecutionEngine`.
* Never hardcode secrets. All configurations must be loaded securely via environment variables.

## 2. Testing & Quality
* All code changes MUST include corresponding tests using the `pytest` framework.
* Ensure code is cleanly modular.
* If a module imports `bot.config`, tests should use `mocker.patch` to set correct namespace defaults rather than modifying the original config.
* CI must always pass before PRs are eligible for auto-merging.

## 3. Autonomous Pipeline
* Jules runs as an automated agent on GitHub Actions (`google-labs-code/jules-action@v1.0.0`).
* A deterministic CI failure workflow (`jules-ci-fixer`) handles repair if CI checks fail.
* Eligible low-risk Jules PRs are auto-merged (`auto-merge-jules.yml`) by Octokit squash merge.
* **High-Risk Path Protection**: Changes to `.github/workflows/`, `AGENTS.md`, or `opencode.json` will block auto-merge and require manual review.

## 4. Development Standards
* Follow structured logging without logging API keys or other sensitive credentials.
* Batch API and broker requests where possible to avoid `O(N)` loop delays.
* The frontend dashboard must remain plain HTML/JS and use sanitization (e.g., `escapeHTML`) when injecting dynamic values into `.innerHTML`.
