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
- **Repo registration (auto).** A repo must be registered with Cyrus once (`cyrus self-add-repo "<url>" "<workspace>"`) — Cyrus only acts on registered repos and uses this as the project→repo map. `/plantask` does this automatically on a project's first run, so it covers BOTH planned and hand-created Linear issues. Per task: nothing — Cyrus worktrees each issue from the existing clone.
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

## Setup gotchas (from live setup, cyrus-ai 0.2.65, macOS)
Things the `/cyrus-setup` skill got wrong on this machine — do these instead:
- **Bootstrap `config.json` first.** `self-auth-linear` and `self-add-repo` both error "Config file not found" and `cyrus start` does NOT create it. Create a minimal one before anything: `printf '{\n  "repositories": []\n}\n' > ~/.cyrus/config.json`.
- **ngrok: don't use the skill's `~/.config/ngrok/ngrok.yml` + `ngrok start cyrus`** — on macOS ngrok reads `~/Library/Application Support/ngrok/ngrok.yml`, so it won't find that tunnel. Instead: `ngrok config add-authtoken <token>` (writes the default config), then start with `ngrok http --domain=<your-static-domain> 3456`. Tunnel must be running during `self-auth-linear` (OAuth callback hits `CYRUS_BASE_URL/callback`) and during operation.
- **`cyrus` lives under nvm** (`~/.nvm/versions/node/vXX/bin`). Ensure the right node is active (`nvm use XX`) or it's `command not found`.
- **Order that actually works:** bootstrap config.json → start ngrok tunnel (→3456) → `cyrus self-auth-linear` (browser Authorize) → `cyrus self-add-repo <url> "<workspace>"` → `cyrus start` (tmux). Secrets (`CLAUDE_CODE_OAUTH_TOKEN`, `LINEAR_*`, ngrok authtoken) go into `~/.cyrus/.env` / ngrok config via the user pasting — never printed.
- **Routing is by LABEL and is evaluated ONCE, at the first agent session.** A repo in `config.json` has `routingLabels` (default `["<repo-name>"]`). An issue routes to that repo only if it carries a Linear **label of that exact name** when Cyrus first opens its session. If no label matches, Cyrus logs `RepositoryRouter: No routing match … requesting user selection` and posts an elicitation comment ("Please reply with an option: <repo-url>") instead of starting. So: **the routing label must exist in Linear and be on the issue BEFORE it's delegated** — that's why `/plantask` now adds `<repo-name>` as a label at creation (fully auto, no elicitation).
- **Adding the label LATER does not re-route.** Routing isn't re-run on label/assignee/delegate updates (delegate can't even be cleared via the Linear MCP). To unstick an already-elicited issue, **reply in the agent-session comment thread** with the repo URL: `save_comment(issueId, parentId=<the "agent session with cyrus" thread comment id>, body="<repo-url>")`. Cyrus parses that reply, routes, creates the worktree, and starts. (Verified: ADM-71 went worktree→opus session this way.)
