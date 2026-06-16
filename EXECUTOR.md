# Executor — Cyrus (adopted, not built)

`/plantask` creates the tasks. **Cyrus** executes them. We adopt Cyrus instead of building an
executor — it already does the hard parts: a local, webhook-triggered runner that spins a git
worktree per Linear issue, runs Claude Code / Codex / Cursor / Gemini on it, and streams progress
back to Linear + opens the PR. Self-hosted on your own machine, bring-your-own-keys.

Source of truth: https://github.com/cyrusagents/cyrus (README, `docs/CONFIG_FILE.md`,
`docs/CLOUDFLARE_TUNNEL.md`). Verify commands there before running — the org/package name has
appeared as both `cyrusagents` and `ceedaragents`; trust the live README.

## Setup (you run these — external code + OAuth, so not the agent)
1. Install the Cyrus skill: `npx skills add ceedaragents/cyrus -g` (external npm — you run it).
2. In any agent, run **`/cyrus-setup`** — its AI-guided onboarding installs deps, creates your
   Linear OAuth app + GitHub App, connects repos, and sets up the tunnel. Follow its prompts.
3. Keep it running: `tmux new -s cyrus` then `cyrus` (or `pm2 start cyrus --name cyrus`).
4. In `config.json`, map each repo to the agent to use (Claude Code / Codex / Cursor) and the
   worktree base. (See `docs/CONFIG_FILE.md`.)

## How it plugs into our loop
- **Trigger = assignment.** Cyrus starts when an issue is assigned to the Cyrus agent. So
  `/plantask` (or you) assigns the feature's tasks to the agent **only after all are created**
  (nuance #1) — nothing runs before the plan is complete.
- **Ordering.** `blockedBy` relations keep blocked tasks from starting; only unblocked sub-issues
  run. Independent (parallel-safe) tasks get their own worktrees.
- **PR linking.** Cyrus opens the PR; ensure `Closes <issue-id>` is in it so Linear links it
  (don't rely on branch-name matching — see the plantask skill).
- **Human gate stays.** PRs are reviewed/merged by you. Cyrus does not merge to main.

## Rate-limit policy (nuance #3 — decided)
On a rate limit, **wait and resume the SAME tool** — do NOT switch Codex↔Claude mid-task
(two half-attempts, wasted budget, fragile cross-tool resume). Reserve a tool switch for a tool
that is hard-down (not just limited). After N failed retries, stop and **escalate**: set the issue
to Blocked + comment for a human. Never loop indefinitely.

## Guardrails / nuances to keep in mind
- **Claim/lock**: an issue moves to In Progress + assignee when picked, so a second trigger can't double-grab it.
- **Concurrency cap**: limit simultaneous worktrees — N parallel agents = real token spend, and PR review is the real ceiling.
- **Per-task verify**: the executor must run that task's Verification (build/test) before opening the PR (our loop's Verify gate). A tool switch never skips it.
- **Resume/state**: partial work survives via the pushed branch + a progress comment on the issue; resume re-reads the issue + branch diff.
- **Machine must be awake**: local execution needs your laptop on with Cyrus running (we chose no heartbeat/cloud). Closed laptop = tasks wait.
- **Security**: Cyrus holds repo + MCP credentials locally; scope them, keep them off any committed file.
