// .github/scripts/auto_merge_policy.js
function evaluateAutoMerge(context, run, prData, files) {
  // 1. Correct repository (not fork)
  if (prData.head.repo.full_name !== context.payload.repository.full_name) {
    return { merged: false, reason: "PR is from a fork. Blocking auto-merge." };
  }

  // 2. Correct production/default base
  const default_branch = context.payload.repository.default_branch;
  if (prData.base.ref !== default_branch) {
    return { merged: false, reason: `PR base is not the default branch (${default_branch}). Blocking auto-merge.` };
  }

  // 3. Not draft
  if (prData.draft) {
    return { merged: false, reason: "PR is a draft. Blocking auto-merge." };
  }

  // 4. Record provenance (observability only)
  const author = prData.user.login;
  let provenance = "unknown";
  if (author === "google-labs-jules[bot]") {
    provenance = "Jules";
  } else if (author.includes("[bot]")) {
    provenance = "other bot";
  } else {
    provenance = "human";
  }
  console.log(`Agent provenance: ${provenance} (Author: ${author})`);

  // 5. Exact SHA validation
  const current_head_sha = prData.head.sha;
  const ci_sha = run.data.head_sha;
  if (current_head_sha !== ci_sha) {
    return { merged: false, reason: `SHA mismatch: PR HEAD ${current_head_sha} != CI SHA ${ci_sha}. Blocking auto-merge.` };
  }

  // 6. No merge conflict
  if (prData.mergeable !== true) {
    return { merged: false, reason: "PR has conflicts or mergeable state is unknown. Blocking auto-merge." };
  }

  // 7. High-risk file check
  const highRiskPatterns = [
    /^\.github\/workflows\/.*/,
    /^AGENTS\.md$/,
    /^opencode\.json$/,
    /^bot\/config\.py$/,
    /auth/,
    /secrets/,
    /migration/,
    /deploy/,
    /infrastructure/,
    /security/,
    /broker/,
    /PAPER_MODE/,
    /permissions/
  ];

  const hasHighRisk = files.some(file =>
    highRiskPatterns.some(pattern => pattern.test(file.filename))
  );

  if (hasHighRisk) {
    return { merged: false, reason: "PR modifies high-risk paths. Blocking auto-merge." };
  }

  // 8. Execute squash merge
  return { merged: true, sha: current_head_sha };
}

module.exports = { evaluateAutoMerge };
