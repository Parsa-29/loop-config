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
  - ⚠️ **A blocked task does NOT auto-start when its blockers reach Done** (Cyrus reacts to
    webhooks, it doesn't watch the dependency graph). After the human merges a blocker's PR,
    re-trigger the now-unblocked dependent: ensure it has the routing label, then reply the repo
    URL in its agent-session thread (or re-delegate). Verified on ADM-74 — it sat in Backlog after
    71/72/73 merged until manually triggered.
- **PR linking.** Cyrus's auto branch (`cyrus/adm-NN-...`) links the PR to that task's OWN sub-issue
  and moves it to Done on merge (branch-name matching works — verified). Each sub-PR closes its own
  issue; **never put `Closes <parent>` in a sub-PR** (it closes the whole feature on first merge).
  Let the parent close via Linear's "complete parent when all sub-issues complete" or only the final task.
- **Repo registration (auto).** A repo must be registered with Cyrus once (`cyrus self-add-repo "<url>" "<workspace>"`) — Cyrus only acts on registered repos and uses this as the project→repo map. `/plantask` does this automatically on a project's first run, so it covers BOTH planned and hand-created Linear issues. Per task: nothing — Cyrus worktrees each issue from the existing clone.
- **Human gate stays.** PRs are reviewed/merged by you. Cyrus does not merge to main.

## Giving a repo its environment (`.env`) — per-repo, no global collisions
A fresh Cyrus worktree is cloned from `origin/main` and has **no `.env`** (gitignored), so build/test/real-API tasks fail without it. Verified mechanism (cyrus 0.40.1):
- `ClaudeRunner.loadRepositoryEnv(worktree)` reads `<worktree>/.env`, `dotenv.parse`s it, and spreads it into the agent's session env at session start (`cyrus-claude-runner/dist/ClaudeRunner.js:359,505`).
- `GitService.createSingleRepoWorktree` runs `WorktreeIncludeService.copyIgnoredFiles(repoPath, worktree)` then `runRepoSetupScript(...)` on every worktree creation (`cyrus-edge-worker/dist/GitService.js:552,558`). `.worktreeinclude` lists gitignored files to copy in (a file must match BOTH `.gitignore` AND `.worktreeinclude`).

**Setup per repo — ONE atomic command (do NOT use the global `~/.cyrus/.env` for app secrets — it collides across projects):**
```
~/loop-config/bin/cyrus-repo-env.sh <repo-name> <path-to-project-.env>
```
It copies `.env` into the clone, `chmod 600`s it, adds `.env` to `.worktreeinclude`, and verifies all three — printing `OK:` only when worktrees will actually receive the env. Idempotent. **Do this in one step, never hand-do the parts** — the failure we hit (`.env` copied but `.worktreeinclude` forgotten → env-less worktrees → backend build/migrate fails) came from doing it piecemeal. Also commit a `.worktreeinclude` containing `.env` to the repo so it survives re-clones. Before dispatching a repo's tasks, re-check: `grep -qxF .env ~/.cyrus/repos/<repo>/.worktreeinclude && ls ~/.cyrus/repos/<repo>/.env`.

Gotchas: `loadRepositoryEnv` runs at **session start**, so a `.env` added mid-session doesn't apply (re-trigger). Scripts that read `process.env` directly (no `dotenv`) still work because Cyrus injects into the process env. Per-worktree deps (`npm ci`) or generated files go in a committed `cyrus-setup.sh` at the repo root (runs after the worktree is created). The global `EdgeConfig.global_setup_script` runs for ALL repos — reserve it for truly cross-repo setup, not per-project env.

## Safety guard — agent must never delete data or do destructive things
Once a repo's real env (live DB/secrets) reaches the worktree, the executor agent could in principle run a destructive command. Lock that down per repo with ONE command:
```
~/loop-config/bin/cyrus-repo-guard.sh <repo-name>
```
Two layers (both written into `~/.cyrus/config.json`, hot-reloaded):
- **`appendInstruction`** (behavioral, primary): never apply migrations to a live DB (offline `prisma migrate diff` only — a human applies); never DELETE/DROP/TRUNCATE/destructive SQL; no `rm -rf`, force-push, branch/remote deletion; no deploys/payments/secret edits/external mutations. Stop and ask in the issue thread instead. Deliverable is a PR a human reviews.
- **`disallowedTools`** (hard SDK backstop): denylist of the obvious destructive commands (`prisma migrate/db push/db execute`, `npm run prisma:*`/`db:reset`/`db:push`, `rm -rf`, `git push -f/--force`).
Apply to EVERY repo at registration (it's a `/plantask` onboarding step). Idempotent. The behavioral layer is what shaped ADM-76 to generate its migration offline and ask the human to apply it.

## Auto-Done on merge → unblock the chain (no Linear GitHub integration needed)
Cyrus's `blockedBy` gate keys off the blocker issue's **Done** state, not the PR merge. Linear only auto-moves an issue to Done on merge if the repo is connected to Linear's GitHub integration — which can't be set up programmatically and may be impossible for repos in other GitHub orgs. Without it, every chain step needs a manual "set Done + re-trigger".

Fix, per repo, installable at onboarding: `~/loop-config/bin/cyrus-repo-linear-done.sh <repo>` commits `.github/workflows/linear-done-on-merge.yml` (template in `loop-config/templates/`). On a merged PR it resolves the issue from the head branch (`issueVcsBranchSearch`, fallback: `ABC-123` regex), finds the team's completed state, and `issueUpdate`s the issue to Done — via the Linear API, so it works for ANY org. One-time activation: add a `LINEAR_API_KEY` repo secret + push/merge the workflow branch. Once the issue flips to Done, Linear emits an issue webhook that reaches Cyrus, which re-checks parked dependents (`Re-prompt on parked session …`) — so the next blocked task can advance hands-off. (Verify this auto-resume on the next chain; if Cyrus still needs a nudge, reply "proceed" in the dependent's thread.)

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
- **Adding the label LATER does not re-route on its own.** Routing isn't re-run on a label/assignee/delegate update (delegate can't even be cleared via the Linear MCP). To unstick an already-elicited issue, **reply in the agent-session comment thread** with the repo URL: `save_comment(issueId, parentId=<the "This thread is for an agent session with cyrus." thread comment id>, body="<repo-url>")`. That reply fires a `prompted` AgentSessionEvent; Cyrus routes, creates the worktree, and starts. (Verified: ADM-71 went worktree→opus session this way.)
- **After a `cyrus` restart, the thread-reply ALONE fails — add the label first.** A restart drops the in-memory elicitation/session state, so a reply logs `No cached repository for prompted webhook … attempting fallback resolution` → and the fallback resolves the repo **by label**. If the issue has no matching routing label, you get `No routing match … requesting user selection` then `Failed to recover … all fallback methods exhausted` and nothing starts. Fix: **add the `<repo-name>` label to the issue, THEN reply the repo URL in the thread** — the fallback now matches the label and routes. (Verified: ADM-72/73 only started after the label was added.) This is the real reason the permanent fix is "label at creation": it survives restarts and never needs a thread reply at all.
