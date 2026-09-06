# Autonomous Development Setup

To use the autonomous Jules automation pipeline, follow these instructions.

## Prerequisites
1.  **JULES_API_KEY**: Ensure this secret is configured in the repository's GitHub Actions secrets.
2.  **Permissions**: Ensure the GitHub Actions have sufficient permissions to read repository contents, create PRs, write issues (for retry tracking), and execute merges via the GitHub REST API.

## Submitting Tasks

Tasks can be submitted directly via the GitHub UI or via the GitHub API, eliminating the need to copy-paste prompts into the Jules website.

### Via GitHub UI
1. Navigate to the **Actions** tab in the repository.
2. Select the **Jules Task Automation** workflow.
3. Click **Run workflow**.
4. Enter your `prompt` (the task description).
5. (Optional) Override the `starting_branch`.
6. Click **Run workflow**.

### Via GitHub API (Future Orchestrators)
An external system can trigger the task by sending a `repository_dispatch` event:

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{
    "event_type": "jules_task",
    "client_payload": {
      "prompt": "Implement a new feature...",
      "starting_branch": ""
    }
  }'
```

## Reviewing Progress
- Jules will automatically create a Pull Request.
- The CI pipeline will validate the changes.
- If CI fails, a fixer job will attempt automatic correction (up to 3 times).
- If CI passes, the auto-merge bot will perform a squash merge, provided the PR passes all strict safety gates (e.g., no high-risk paths modified).

Manual intervention is only required if:
- The task modifies high-risk paths (e.g., CI workflows, security config).
- CI fails more than 3 times.
- There are merge conflicts.
