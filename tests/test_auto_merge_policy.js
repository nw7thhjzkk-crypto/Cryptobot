const assert = require('assert');
const { evaluateAutoMerge } = require('../.github/scripts/auto_merge_policy.js');

// Helper to create a base mock context
function createMockContext(overrides = {}) {
  const base = {
    context: {
      payload: {
        repository: {
          full_name: 'test/repo',
          default_branch: 'main'
        }
      }
    },
    run: {
      data: {
        head_sha: 'abc1234'
      }
    },
    prData: {
      head: { repo: { full_name: 'test/repo' }, sha: 'abc1234' },
      base: { ref: 'main' },
      draft: false,
      user: { login: 'some-user' },
      mergeable: true
    },
    files: [
      { filename: 'src/main.py' }
    ]
  };

  // Deep merge overrides
  const result = JSON.parse(JSON.stringify(base));

  if (overrides.prData) {
      if (overrides.prData.head) {
          result.prData.head = { ...result.prData.head, ...overrides.prData.head };
          if (overrides.prData.head.repo) {
              result.prData.head.repo = { ...result.prData.head.repo, ...overrides.prData.head.repo };
          }
      }
      if (overrides.prData.base) {
          result.prData.base = { ...result.prData.base, ...overrides.prData.base };
      }
      if (overrides.prData.user) {
          result.prData.user = { ...result.prData.user, ...overrides.prData.user };
      }
      if (overrides.prData.draft !== undefined) result.prData.draft = overrides.prData.draft;
      if (overrides.prData.mergeable !== undefined) result.prData.mergeable = overrides.prData.mergeable;
  }

  if (overrides.run) Object.assign(result.run, overrides.run);
  if (overrides.files) result.files = overrides.files;

  return result;
}

// Tests
console.log("Running auto-merge policy tests...");

// A. Jules PR, same repo, correct base, CI green, exact SHA, low risk -> AUTO-MERGE
let mock = createMockContext({
    prData: { user: { login: 'google-labs-jules[bot]' } }
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, true, "Test A failed");

// B. Other coding-agent PR -> AUTO-MERGE
mock = createMockContext({
    prData: { user: { login: 'some-other[bot]' } }
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, true, "Test B failed");

// C. Human PR -> AUTO-MERGE
mock = createMockContext({
    prData: { user: { login: 'human-user' } }
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, true, "Test C failed");

// D. Fork PR -> BLOCK
mock = createMockContext({
    prData: { head: { repo: { full_name: 'fork/repo' } } }
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, false, "Test D failed");

// F. Wrong base branch -> BLOCK
mock = createMockContext({
    prData: { base: { ref: 'feature-branch' } }
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, false, "Test F failed");

// G. Draft -> BLOCK
mock = createMockContext({
    prData: { draft: true }
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, false, "Test G failed");

// K. SHA mismatch -> BLOCK
mock = createMockContext({
    prData: { head: { sha: 'diff-sha' } }
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, false, "Test K failed");

// L. Merge conflict -> BLOCK
mock = createMockContext({
    prData: { mergeable: false }
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, false, "Test L failed");

// M. High-risk protected change -> BLOCK
mock = createMockContext({
    files: [{ filename: '.github/workflows/test.yml' }]
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, false, "Test M failed");

mock = createMockContext({
    files: [{ filename: 'AGENTS.md' }]
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, false, "Test M (AGENTS.md) failed");

mock = createMockContext({
    files: [{ filename: 'bot/config.py' }]
});
assert.strictEqual(evaluateAutoMerge(mock.context, mock.run, mock.prData, mock.files).merged, false, "Test M (bot/config.py) failed");

console.log("All auto-merge policy tests passed.");