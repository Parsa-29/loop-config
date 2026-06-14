#!/usr/bin/env bash
# loop-skills - keep one shared Agent Skills store synced across local agents.
#
# Default:
#   validate and adopt new real skill directories, then relink canonical skills.
#
# Usage:
#   bin/loop-skills.sh             # adopt valid new skills + relink everywhere
#   bin/loop-skills.sh --dry-run   # show planned changes without changing files
#   bin/loop-skills.sh --stage     # sync, then git add skills/ for review

set -euo pipefail

ROOT="${LOOP_CONFIG_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
STORE="${LOOP_SKILLS_STORE:-$ROOT/skills}"

ADOPT_FROM=(
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
  "$HOME/.codex/skills"
  "$HOME/.cursor/skills"
)

LINK_TO=(
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

dry_run=0
stage=0

usage() {
  sed -n '1,12p' "$0" | sed 's/^# \{0,1\}//'
}

for arg in "$@"; do
  case "$arg" in
    --dry-run)
      dry_run=1
      ;;
    --stage)
      stage=1
      ;;
    --commit)
      echo "error: --commit was removed because it pushed automatically."
      echo "Use --stage, review the diff, then commit/push yourself."
      exit 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $arg"
      usage
      exit 2
      ;;
  esac
done

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

run_or_print() {
  if [ "$dry_run" -eq 1 ]; then
    printf 'dry-run:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

mkdir_store() {
  if [ "$dry_run" -eq 1 ]; then
    [ -d "$STORE" ] || echo "dry-run: mkdir -p $STORE"
  else
    mkdir -p "$STORE"
  fi
}

clean_git_metadata() {
  local skill_dir="$1"
  local found=0

  while IFS= read -r path; do
    [ -n "$path" ] || continue
    found=1
    run_or_print rm -rf "$path"
  done < <(find "$skill_dir" -mindepth 1 -maxdepth 2 -name .git -type d -prune 2>/dev/null || true)

  while IFS= read -r path; do
    [ -n "$path" ] || continue
    found=1
    run_or_print rm -f "$path"
  done < <(find "$skill_dir" -mindepth 1 -name .gitignore -type f 2>/dev/null || true)

  if [ "$found" -eq 1 ]; then
    echo "cleaned git metadata in: $skill_dir"
  fi
  return 0
}

mkdir_store

adopted=0
skipped=0
linked=0
conflicts=0

echo "Store: $STORE"

# 1) Adopt valid real skill directories from known local skill locations.
for source_dir in "${ADOPT_FROM[@]}"; do
  [ -d "$source_dir" ] || continue

  for path in "$source_dir"/*; do
    [ -e "$path" ] || continue
    name="$(basename "$path")"

    if is_excluded "$name"; then
      skipped=$((skipped + 1))
      echo "skip excluded: $path"
      continue
    fi

    if [ -L "$path" ] || [ ! -d "$path" ]; then
      continue
    fi

    if [ ! -f "$path/SKILL.md" ]; then
      skipped=$((skipped + 1))
      echo "skip invalid skill (missing SKILL.md): $path"
      continue
    fi

    if ! has_valid_skill_metadata "$path/SKILL.md"; then
      skipped=$((skipped + 1))
      echo "skip invalid skill metadata: $path/SKILL.md"
      continue
    fi

    if [ -e "$STORE/$name" ]; then
      conflicts=$((conflicts + 1))
      echo "conflict: '$name' exists in store and $source_dir; left installed dir untouched."
      continue
    fi

    run_or_print mv "$path" "$STORE/$name"
    adopted=$((adopted + 1))
    echo "adopted: $name (from $source_dir)"

    if [ "$dry_run" -eq 1 ]; then
      clean_git_metadata "$path"
    else
      clean_git_metadata "$STORE/$name"
    fi
  done
done

# 2) Symlink every canonical skill into each local skill location.
for target_dir in "${LINK_TO[@]}"; do
  if [ "$dry_run" -eq 1 ]; then
    [ -d "$target_dir" ] || echo "dry-run: mkdir -p $target_dir"
  else
    mkdir -p "$target_dir"
  fi

  for skill in "$STORE"/*/; do
    [ -d "$skill" ] || continue
    name="$(basename "$skill")"
    link="$target_dir/$name"

    if [ -L "$link" ] || [ ! -e "$link" ]; then
      run_or_print ln -sfn "$skill" "$link"
      linked=$((linked + 1))
    elif [ -d "$link" ]; then
      echo "skip link conflict: '$name' is a real dir in $target_dir."
    else
      echo "skip link conflict: '$link' exists and is not a directory/symlink."
    fi
  done
done

if [ "$stage" -eq 1 ]; then
  if [ "$dry_run" -eq 1 ]; then
    echo "dry-run: git -C $ROOT add skills"
  else
    git -C "$ROOT" add skills
    echo "staged: skills/"
  fi
fi

echo "summary: adopted=$adopted linked=$linked skipped=$skipped conflicts=$conflicts dry_run=$dry_run"
