#!/usr/bin/env bash
# check-loop-config - read-only health check for loop-config.

set -euo pipefail

ROOT="${LOOP_CONFIG_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
STORE="${LOOP_SKILLS_STORE:-$ROOT/skills}"

SKILL_DIRS=(
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
  "$HOME/.codex/skills"
  "$HOME/.cursor/skills"
)

EXCLUDE=(
  ".DS_Store"
  ".system"
  "codex-primary-runtime"
  "plugins"
  "cache"
)

failures=0
warnings=0

ok() { echo "ok: $*"; }
warn() { warnings=$((warnings + 1)); echo "warn: $*"; }
fail() { failures=$((failures + 1)); echo "fail: $*"; }

is_excluded() {
  local name="$1"
  local excluded
  for excluded in "${EXCLUDE[@]}"; do
    [ "$name" = "$excluded" ] && return 0
  done
  return 1
}

has_valid_skill_metadata() {
  local skill_md="$1"
  [ -f "$skill_md" ] || return 1
  awk '
    NR == 1 && $0 == "---" { fm = 1; next }
    fm && $0 == "---" { exit }
    fm && /^name:[[:space:]]*[^[:space:]]/ { name = 1 }
    fm && /^description:/ { description = 1 }
    END { exit !(name && description) }
  ' "$skill_md"
}

if bash -n "$ROOT/bin/loop-skills.sh"; then
  ok "bin/loop-skills.sh syntax"
else
  fail "bin/loop-skills.sh syntax"
fi

if python3 -m json.tool "$ROOT/claude/settings.ask.json" >/dev/null; then
  ok "claude/settings.ask.json parses"
else
  fail "claude/settings.ask.json does not parse"
fi

if python3 -m json.tool "$ROOT/claude/settings.hooks.json" >/dev/null; then
  ok "claude/settings.hooks.json parses"
else
  fail "claude/settings.hooks.json does not parse"
fi

if python3 "$ROOT/hooks/test_safety_guard.py" >/dev/null 2>&1; then
  ok "hooks/safety_guard.py tests pass"
else
  fail "hooks/safety_guard.py tests fail (run: python3 $ROOT/hooks/test_safety_guard.py)"
fi

if [ -f "$HOME/.claude/settings.json" ] && grep -q "loop-config/hooks/safety_guard.py" "$HOME/.claude/settings.json"; then
  ok "safety guard is wired into ~/.claude/settings.json"
else
  warn "safety guard is not wired into ~/.claude/settings.json (README: Safety hooks)"
fi

if python3 - "$ROOT/codex/config.gate.toml" <<'PY'
import sys, tomllib
with open(sys.argv[1], "rb") as f:
    tomllib.load(f)
PY
then
  ok "codex/config.gate.toml parses"
else
  fail "codex/config.gate.toml does not parse"
fi

for skill in "$STORE"/*; do
  [ -e "$skill" ] || continue
  [ -d "$skill" ] || continue
  name="$(basename "$skill")"

  if ! has_valid_skill_metadata "$skill/SKILL.md"; then
    fail "invalid canonical skill metadata: $skill"
  fi

  for target_dir in "${SKILL_DIRS[@]}"; do
    [ -d "$target_dir" ] || continue
    link="$target_dir/$name"
    if [ ! -e "$link" ]; then
      warn "canonical skill not linked into $target_dir: $name"
    elif [ -L "$link" ] && [ "$(readlink "$link")" != "$skill/" ] && [ "$(readlink "$link")" != "$skill" ]; then
      warn "skill link points elsewhere: $link -> $(readlink "$link")"
    elif [ -e "$link" ] && [ ! -L "$link" ]; then
      warn "canonical skill has real-dir conflict in $target_dir: $name"
    fi
  done
done

for source_dir in "${SKILL_DIRS[@]}"; do
  [ -d "$source_dir" ] || continue

  for skill in "$source_dir"/*; do
    [ -e "$skill" ] || continue
    name="$(basename "$skill")"
    is_excluded "$name" && continue
    [ -d "$skill" ] || continue

    if [ ! -e "$STORE/$name" ]; then
      if [ -L "$skill" ]; then
        warn "installed skill link is missing from store: $skill"
      elif has_valid_skill_metadata "$skill/SKILL.md"; then
        warn "installed real skill is not adopted into store: $skill"
      else
        warn "installed real skill is invalid and not adopted: $skill"
      fi
    fi
  done
done

if [ "$failures" -gt 0 ]; then
  echo "summary: failures=$failures warnings=$warnings"
  exit 1
fi

echo "summary: failures=0 warnings=$warnings"
