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

**Don't assume** - state your assumptions; if something is unclear, stop and ask; if multiple readings exist, present them, don't pick silently; push back when warranted. (Karpathy's rule.)

## Use what already exists
Before writing anything from scratch, check for an existing skill, tool, command, or MCP
server that fits — and use it. Don't reinvent capabilities the agent already has.

## The coding flow (multi-step tasks): plan → worktree → verify → PR
For any non-trivial task, follow this flow using the installed skills (don't improvise it):
1. **Plan** — `writing-plans` (and `brainstorming` if the goal is fuzzy). Output: files, steps, risks, the Done check.
2. **Isolate** — `using-git-worktrees` for feature work; `dispatching-parallel-agents` / `subagent-driven-development` when 2+ tasks are independent.
3. **Build test-first** — `test-driven-development`.
4. **Verify** — `verification-before-completion`: run the project's verify gate from its instructions file (build + tests + lint; backend AND frontend; run the app for UI) and confirm real output before claiming done.
5. **Review + integrate** — `requesting-code-review`, then `finishing-a-development-branch` to open the PR. After the PR is open, move the linked tracker issue to **In Review** (prefer the tracker's native PR automation; otherwise set it explicitly). The human approves the PR (the gate). `receiving-code-review` when acting on feedback.
Stuck? `systematic-debugging`.

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
