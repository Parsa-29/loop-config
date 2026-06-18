#!/usr/bin/env bash
# cyrus-repo-linear-done.sh — install the "PR merged → Linear issue Done" GitHub Action into a repo.
#
# Makes auto-Done-on-merge work for ANY repo/org WITHOUT Linear's GitHub integration
# (which can't be connected programmatically). Cyrus then re-checks parked dependents on the
# Done webhook, so the dependency chain can advance without a manual Done + re-trigger.
#
# Stages the workflow on a branch and COMMITS it — does NOT push (push is approval-gated).
# Usage: cyrus-repo-linear-done.sh <repo-name>
set -euo pipefail
REPO="${1:?usage: cyrus-repo-linear-done.sh <repo-name>}"
CLONE="$HOME/.cyrus/repos/$REPO"
TMPL="$HOME/loop-config/templates/linear-done-on-merge.yml"
BRANCH="loop/linear-done-on-merge"

[ -d "$CLONE/.git" ] || { echo "FAIL: clone not found at $CLONE — run 'cyrus self-add-repo' first."; exit 1; }
[ -f "$TMPL" ]       || { echo "FAIL: template missing at $TMPL"; exit 1; }

cd "$CLONE"
git fetch origin --quiet || true
git checkout -B "$BRANCH" origin/HEAD 2>/dev/null || git checkout -B "$BRANCH"
mkdir -p .github/workflows
cp "$TMPL" .github/workflows/linear-done-on-merge.yml
git add .github/workflows/linear-done-on-merge.yml
if git diff --cached --quiet; then
  echo "OK: workflow already present and unchanged on $BRANCH (idempotent)."
else
  git -c user.name="loop-config" -c user.email="noreply@local" commit -q -m "ci: move linked Linear issue to Done on PR merge"
  echo "OK: committed workflow on branch '$BRANCH' in $CLONE."
fi
echo
echo "ACTIVATE (one-time per repo):"
echo "  1. Add repo secret LINEAR_API_KEY (GitHub → repo Settings → Secrets and variables → Actions)."
echo "     Key from Linear → Settings → Security & access → Personal API keys."
echo "  2. Push + merge this branch:  git -C $CLONE push origin $BRANCH   then open/merge a PR (or push to the default branch)."
echo "  After that, every merged PR whose branch carries the issue id auto-moves the issue to Done."
