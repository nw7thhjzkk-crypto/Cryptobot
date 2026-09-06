# Autonomous Development

Cryptobot uses a robust autonomous development framework to continuously integrate improvements.

## Jules Integration
Jules is the primary implementation agent, configured in `.github/workflows/jules.yml`. It operates on the repository's dynamic default branch and creates standard PRs.

## The Fixer Loop
If an autonomous PR breaks tests or linting, the `Jules CI Failure Fixer` workflow catches the failure event and creates a follow-up task for Jules to fix the breaking commit. This prevents CI failures from blocking development and ensures the agent self-corrects.

## Security Controls
- **High-Risk Files**: AI cannot automatically merge changes to workflows or the `AGENTS.md` definition file.
- **Fail-Closed Design**: If branch validation, SHA matching, or provenance cannot be perfectly verified, the PR auto-merge defaults to `FAIL_CLOSED`.
- **Pre-commit Verifications**: Jules relies on local validation before creating PRs.
