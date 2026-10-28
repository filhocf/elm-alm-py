#!/usr/bin/env bash
# tests-prove-fix: a changed test must FAIL against the base branch (without the
# PR's source change). This proves the test is load-bearing — it catches the
# regression it claims to — instead of a test that passes no matter what.
#
# Usage: check_tests_prove_fix.sh <base-ref>   (e.g. origin/main)
#
# How it works:
#   1. Find test files changed in this PR vs the base.
#   2. Find non-test source changed in this PR vs the base.
#   3. Stash the PR's source change back to the base version, keep the new tests.
#   4. Run the changed tests. They MUST fail (red) — if they pass without the
#      source change, they do not prove the fix. Restore everything afterwards.
#
# If the PR changes no tests, or changes no source, there is nothing to prove:
# the check passes (a docs-only or test-only PR is not in scope here).
set -euo pipefail

BASE="${1:?usage: check_tests_prove_fix.sh <base-ref>}"

changed_tests=$(git diff --name-only --diff-filter=AM "$BASE"...HEAD -- 'tests/**/*.py' | grep -v '__init__' || true)
changed_src=$(git diff --name-only --diff-filter=AM "$BASE"...HEAD -- 'src/**/*.py' || true)

if [ -z "$changed_tests" ]; then
  echo "prove-fix: no changed test files — nothing to prove."
  exit 0
fi
if [ -z "$changed_src" ]; then
  echo "prove-fix: no changed source files — nothing to prove (test-only change)."
  exit 0
fi

echo "Changed tests:"; echo "$changed_tests"
echo "Changed source (will be reverted to base for the probe):"; echo "$changed_src"

# Revert ONLY the source to the base version; keep the PR's tests in place.
# shellcheck disable=SC2086
git checkout "$BASE" -- $changed_src

cleanup() {
  # Restore the PR's source from HEAD (index + worktree).
  # shellcheck disable=SC2086
  git checkout HEAD -- $changed_src
}
trap cleanup EXIT

echo "Running changed tests against base source — they MUST fail..."
# shellcheck disable=SC2086
if uv run pytest $changed_tests -q; then
  echo "::error::prove-fix FAILED — the changed tests PASS without the source change."
  echo "A test that passes without its fix does not prove the fix. Make it red on base first."
  exit 1
fi

echo "prove-fix OK — changed tests fail on base, as required."
