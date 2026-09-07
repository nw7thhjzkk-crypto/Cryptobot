# AI Engineering Workflow

This document outlines the autonomous development pipeline used in this repository.

## Overview
The goal is to enable fully autonomous code generation, testing, and merging without requiring manual interaction with the Jules website.

## Pipeline Steps

### 1. Task Submission
An external orchestrator (like a future Grok integration) or a human user submits a task payload to GitHub.
- **Trigger:** GitHub Actions `workflow_dispatch` or `repository_dispatch`.
- **Action:** `.github/workflows/jules.yml` uses the official `google-labs-code/jules-invoke@v1` action to send the task and starting branch to Jules.

### 2. Implementation & PR Creation
Jules processes the task, creates a branch based on the default branch, implements the changes, and automatically opens a Pull Request.

### 3. Continuous Integration (CI)
The `.github/workflows/ci.yml` workflow triggers on the new PR.
- Runs `flake8` for linting.
- Runs `pytest` for unit testing.
- Uses dummy environment variables for secrets to safely evaluate the PR.

### 4. Auto-Repair (Jules CI Fixer)
If the CI workflow fails:
- **Trigger:** `.github/workflows/jules-ci-fixer.yml` detects the failure.
- **Action:** It verifies the PR was created by Jules and sends a follow-up prompt to fix the errors.
- **Recursion Protection:** The fixer is limited to 3 attempts per PR to prevent infinite loops.

### 5. Auto-Merge Safety Gates
If the CI workflow passes:
- **Trigger:** `.github/workflows/auto-merge-eligible-prs.yml` detects the success.
- **Action:** A GitHub script evaluates strict safety conditions:
  1.  **Repository:** Must be the same repository (no forks).
  2.  **Base Branch:** Must target the dynamic default/production branch.
  3.  **Draft Status:** PR must not be a draft.
  4.  **Exact SHA Match:** The current HEAD SHA of the PR must exactly match the SHA that passed CI.
  5.  **Conflicts:** The PR must be mergeable (no conflicts).
  6.  **High-Risk Paths:** The PR must not modify critical infrastructure, CI workflows, or security files (e.g., `.github/workflows/**`, `AGENTS.md`).

### 6. Squash Merge
If all safety gates pass, the PR is automatically squash-merged into the default branch using the GitHub API, specifying the exact validated SHA.
