# AI Engineering Workflow

This document explains the autonomous engineering pipeline for Cryptobot.

## Pipeline Overview
The pipeline enables autonomous agents to solve issues, write tests, and integrate features securely.

1. **Task Trigger**: A comment mentioning `@jules` or a manual workflow dispatch starts the `Jules Autonomous Engineering` workflow.
2. **Implementation**: Jules (using the `google-labs-code/jules-action@v1.0.0`) checks out the code, applies changes, runs local verifications, and creates a PR.
3. **Continuous Integration (CI)**: The PR triggers the `CI Pipeline`, which runs `pytest` and `flake8` syntax checks.
4. **Jules CI Failure Fixer**: If the CI fails on a Jules PR, a workflow prompts Jules to repair the CI failure automatically.
5. **Deterministic Safety Gates & Auto-Merge**: If the CI succeeds, the `Autonomous Jules PR Auto-Merge` workflow assesses the PR:
   - Validates the base branch, repository, PR state, and Jules provenance.
   - Enforces exact SHA matching to prevent stale CI results.
   - Rejects auto-merging for high-risk files (`.github/workflows/`, `AGENTS.md`, etc.).
   - If eligible, performs a squash merge via the GitHub REST API.

This completely automates low-risk development while providing strict security boundaries.
