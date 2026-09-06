# AGENTS.md

## High-Risk Paths
The following files and directories are considered high-risk and MUST NOT be auto-merged by AI agents without manual human review:
- `.github/workflows/**` (All CI/CD configurations)
- `AGENTS.md` (This file)
- `opencode.json` (Project metadata)
- `bot/config.py` (Secrets and authentication configuration)
- Any files related to migrations, authentication, authorization, deployment, infrastructure, security, secrets, broker execution, PAPER_MODE, and permissions.

## Jules Automation Flow
This repository uses an end-to-end GitHub-native automation pipeline for Jules:
1. **Task Submission:** Tasks are submitted via the `Jules Task Automation` GitHub Action (`.github/workflows/jules.yml`), which can be triggered manually (`workflow_dispatch`) or via API (`repository_dispatch`).
2. **Jules Execution:** Jules receives the task, creates a branch from the main/production branch, implements the requested changes, and opens a Pull Request.
3. **CI Validation:** The `CI` workflow (`.github/workflows/ci.yml`) automatically runs tests and linters.
4. **Auto-Repair:** If CI fails, the `Jules CI Fixer` workflow (`.github/workflows/jules-ci-fixer.yml`) prompts Jules to fix the errors, up to a maximum of 3 retries to prevent recursion.
5. **Auto-Merge:** If CI passes, the `Auto-merge eligible PRs` workflow (`.github/workflows/auto-merge-eligible-prs.yml`) evaluates strict deterministic gates. If all conditions (exact SHA match, no conflicts, no high-risk files modified, correct repository, etc.) are met, the PR is automatically squash-merged.
