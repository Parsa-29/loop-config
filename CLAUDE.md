# Global working method — Loop Engineering

Apply this to every project. Keep it short on purpose (loads into every session).

## The loop (every task)
1. **Observe** — read the relevant code + the project's CLAUDE.md before editing. Say which files you'll touch.
2. **Decide** — for non-trivial work, give a short plan (files, steps, risks, how you'll verify) and get my approval before writing. Use plan mode for complex tasks.
3. **Act** — smallest viable steps.
4. **Verify** — never say "done" until build + tests + lint pass for what you touched (commands live in that project's CLAUDE.md). Report real output. For UI/runtime, actually run it.
5. **Learn** — save non-obvious decisions to memory; keep CLAUDE.md current.

## Use what already exists
Before writing anything from scratch, check for an existing **skill, MCP tool, or agent** that fits — and use it. Don't reinvent capabilities the harness already has.

## Human approval (ask before running, never autonomous)
DB writes/migrations · `git push` · deploys · live external mutations (payments, sending messages/email, publishing ads) · dependency additions · secret/`.env` edits.
Read-only work (reading, local builds, tests, dev servers, drafts) is autonomous.

## How to give me a task
Small (most cases):
```
Service: <which repo>
Goal: <one sentence>
Done: <a checkable condition — test passes / endpoint returns X / UI behaves so>
```
Big or risky — add: context (files/module), constraints (don't touch X), verify command, risk (DB/push/external?).

Rule that matters most: **always include a Done criterion.** No Done = the loop has no stop condition.

## Keep this lean
This file and project CLAUDE.md load every session and compete with real work for context. Keep each tight; put long/rare detail in separate docs and link them, don't inline.
