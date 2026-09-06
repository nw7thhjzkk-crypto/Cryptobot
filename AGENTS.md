# Autonomous Engineering Rules for Jules and AI Agents

1. Work from the current production branch.
2. Understand the existing architecture before changing code.
3. Make the smallest correct change.
4. Never fabricate integrations.
5. Never fabricate successful tests.
6. Never commit secrets.
7. Never weaken authentication or authorization.
8. Never disable security controls merely to make CI pass.
9. Run appropriate lint/typecheck/test/build commands.
10. Fix failures before creating the PR.
11. Preserve existing functionality.
12. Avoid unrelated refactoring.
13. Create focused PRs.
14. Clearly describe:
    - what changed
    - why
    - tests run
    - known limitations
15. Never modify unrelated files.
16. Never bypass CI.
17. Never manually merge its own PR.
18. Do not treat AI-generated approval as a substitute for deterministic security gates.
19. Never modify autonomous-merge safeguards simply to make a PR merge.
20. When a change is high-risk, leave it for human review.
