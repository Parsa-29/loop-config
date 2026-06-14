#!/usr/bin/env bash
# loop-skills — keep one shared Agent-Skills store synced across Claude / Codex / Cursor.
#
# What it does (idempotent, safe to run anytime):
#   1. ADOPT  — any newly-installed skill that landed as a REAL dir in a tool's skills
#               folder is moved into the canonical store (~/loop-config/skills).
#   2. SYNC   — every canonical skill is symlinked into all three tools' skills folders.
#
# Usage:
#   bin/loop-skills.sh            # adopt new + relink everywhere (no git)
#   bin/loop-skills.sh --commit   # also git add/commit/push the store
#
# Tool built-ins are never touched (see EXCLUDE).

set -euo pipefail

STORE="$HOME/loop-config/skills"
TOOLS=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.cursor/skills")
EXCLUDE=("codex-primary-runtime" ".system" ".DS_Store")

is_excluded() { local n="$1"; for e in "${EXCLUDE[@]}"; do [ "$n" = "$e" ] && return 0; done; return 1; }

mkdir -p "$STORE"
adopted=0 linked=0

# 1) ADOPT — move real (non-symlink) skill dirs from tools into the canonical store
for tool in "${TOOLS[@]}"; do
  [ -d "$tool" ] || continue
  for path in "$tool"/*; do
    [ -e "$path" ] || continue
    name="$(basename "$path")"
    is_excluded "$name" && continue
    # only real directories (skip symlinks and files)
    if [ -d "$path" ] && [ ! -L "$path" ]; then
      if [ -e "$STORE/$name" ]; then
        echo "⚠️  conflict: '$name' exists in both $tool and the store — left in place, resolve by hand."
        continue
      fi
      mv "$path" "$STORE/$name"
      echo "📦 adopted: $name  (from $tool)"
      adopted=$((adopted+1))
    fi
  done
done

# strip nested git artifacts that would break the parent repo / hide files
find "$STORE" -name .git -maxdepth 2 -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$STORE" -name .gitignore -type f -delete 2>/dev/null || true

# 2) SYNC — symlink every canonical skill into each tool
for tool in "${TOOLS[@]}"; do
  mkdir -p "$tool"
  for skill in "$STORE"/*/; do
    [ -d "$skill" ] || continue
    name="$(basename "$skill")"
    link="$tool/$name"
    if [ -L "$link" ] || [ ! -e "$link" ]; then
      ln -sfn "$skill" "$link"; linked=$((linked+1))
    elif [ -d "$link" ]; then
      echo "⚠️  '$name' is a real dir in $tool (not adopted) — skipping symlink."
    fi
  done
done

echo "✅ adopted $adopted new skill(s); ensured $linked symlink(s) across ${#TOOLS[@]} tools."

# optional: version it
if [ "${1:-}" = "--commit" ]; then
  cd "$HOME/loop-config"
  git add skills
  if git diff --cached --quiet; then
    echo "nothing new to commit."
  else
    git commit -q -m "skills: adopt + sync ($(git diff --cached --name-only | wc -l | tr -d ' ') paths)"
    git push origin main
    echo "pushed."
  fi
fi
