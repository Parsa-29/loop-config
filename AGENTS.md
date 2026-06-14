# Working method — Loop Engineering

Agent-neutral. This is the single source of truth; each tool reads a copy/symlink of it
(Claude Code → CLAUDE.md, Codex → AGENTS.md, Cursor → rule / User Rules). Keep it short on
purpose — it loads into every session and competes with real work for context.

## The loop (every task)
1. **Observe** — read the relevant code + the project's instructions file before editing. Say which files you'll touch.
2. **Decide** — for non-trivial work, give a short plan (files, steps, risks, how you'll verify) and get approval before writing. Use a planning step / plan mode if the agent has one.
3. **Act** — smallest viable steps.
4. **Verify** — never say "done" until build + tests + lint pass for what you touched (commands live in the project's instructions file). Report real output. For UI/runtime, actually run it.
5. **Learn** — record non-obvious decisions where the agent persists memory; keep the instructions file current.

## Use what already exists
Before writing anything from scratch, check for an existing skill, tool, command, or MCP
server that fits — and use it. Don't reinvent capabilities the agent already has.

## Human approval (ask before running, never autonomous)
DB writes/migrations · `git push` · deploys · live external mutations (payments, sending
messages/email, publishing ads) · dependency additions · secret/`.env` edits.
Read-only work (reading, local builds, tests, dev servers, drafts) is autonomous.

## How to give the agent a task
Small (most cases):
```
Service: <which repo>
Goal: <one sentence>
Done: <a checkable condition — test passes / endpoint returns X / UI behaves so>
```
Big or risky — add: context (files/module), constraints (don't touch X), verify command, risk (DB/push/external?).

Rule that matters most: **always include a Done criterion.** No Done = the loop has no stop condition.

## Keep this lean
This file and the project instructions file load every session. Keep each tight; put
long/rare detail in separate docs and link them, don't inline.
