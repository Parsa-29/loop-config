#!/usr/bin/env bash
# cyrus-repo-env.sh — give a Cyrus-managed repo its .env, atomically and idempotently.
#
# Does ALL of the onboarding in one step so it can't be done half-way:
#   1. copies the project .env into the base clone (~/.cyrus/repos/<repo>/.env), chmod 600
#   2. ensures `.env` is listed in that clone's .worktreeinclude
#   3. verifies both are in place AND .env is gitignored (required for Cyrus to copy it)
#
# Cyrus then copies .env into every worktree (GitService.copyIgnoredFiles) and loads it into
# the agent's session env (ClaudeRunner.loadRepositoryEnv). Per-repo, no global collisions.
#
# Usage:  cyrus-repo-env.sh <repo-name> </path/to/project/.env>
# Secrets: copies file->file only; never prints values.
set -euo pipefail

REPO="${1:?usage: cyrus-repo-env.sh <repo-name> <path-to-.env>}"
SRC="${2:?usage: cyrus-repo-env.sh <repo-name> <path-to-.env>}"
CLONE="$HOME/.cyrus/repos/$REPO"

[ -d "$CLONE" ]   || { echo "FAIL: clone not found at $CLONE — run 'cyrus self-add-repo' first."; exit 1; }
[ -f "$SRC" ]     || { echo "FAIL: source .env not found at $SRC"; exit 1; }

cp "$SRC" "$CLONE/.env"
chmod 600 "$CLONE/.env"

WI="$CLONE/.worktreeinclude"
grep -qxF ".env" "$WI" 2>/dev/null || printf '.env\n' >> "$WI"

# Verify (necessary + sufficient for Cyrus to copy .env into worktrees)
ok=1
[ -f "$CLONE/.env" ]                         || { echo "VERIFY FAIL: .env not in clone"; ok=0; }
grep -qxF ".env" "$WI" 2>/dev/null           || { echo "VERIFY FAIL: .env not in .worktreeinclude"; ok=0; }
( cd "$CLONE" && git check-ignore .env >/dev/null 2>&1 ) || { echo "VERIFY FAIL: .env not gitignored in repo — Cyrus copies a file only if it matches BOTH .gitignore AND .worktreeinclude"; ok=0; }

if [ "$ok" = 1 ]; then
  echo "OK: $REPO env onboarded — $(grep -c '=' "$CLONE/.env") vars, .worktreeinclude lists .env, gitignored. Worktrees will auto-receive it."
else
  echo "INCOMPLETE: fix the above before dispatching $REPO tasks."; exit 1
fi
