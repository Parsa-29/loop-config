# loop-config

Portable, **agent-neutral** Loop Engineering working setup. One source of truth
(`AGENTS.md`), bridged to each AI coding agent so you always develop in the
Observe → Decide → Act → Verify → Learn loop — in Claude Code, Codex, Cursor, or any
tool that reads `AGENTS.md`.

## Source of truth
- **`AGENTS.md`** — the working method + task template + tool-reuse rule. Edit this one
  file; every agent gets a copy/symlink of it. `AGENTS.md` is the cross-tool standard
  (Codex, Cursor, Copilot, Windsurf, Cline read it directly). Claude Code is the only one
  that needs its own filename (`CLAUDE.md`).

## Per-agent setup

### Claude Code
Reads `CLAUDE.md`, not `AGENTS.md`. Copy (or symlink) the manual and merge the gate:
```bash
cp ~/loop-config/AGENTS.md ~/.claude/CLAUDE.md          # global, all projects
# (or: ln -sf ~/loop-config/AGENTS.md ~/.claude/CLAUDE.md  for auto-sync)

# merge the approval gate into ~/.claude/settings.json (preserves your allow list)
node -e '
  const fs=require("fs"), os=require("os"), path=require("path");
  const p=path.join(os.homedir(),".claude","settings.json");
  const ask=JSON.parse(fs.readFileSync(path.join(os.homedir(),"loop-config","claude","settings.ask.json"),"utf8")).permissions.ask;
  let s={}; try{ s=JSON.parse(fs.readFileSync(p,"utf8")); }catch{}
  s.permissions=s.permissions||{};
  s.permissions.ask=Array.from(new Set([...(s.permissions.ask||[]), ...ask]));
  fs.mkdirSync(path.dirname(p),{recursive:true});
  fs.writeFileSync(p, JSON.stringify(s,null,2)+"\n");
  console.log("merged",ask.length,"ask rules");
'
```

### Codex
Reads `AGENTS.md` natively.
```bash
cp ~/loop-config/AGENTS.md ~/.codex/AGENTS.md           # global guidance, all projects
```
Approval gate: open `codex/config.gate.toml` and **merge** the two keys into
`~/.codex/config.toml` (`approval_policy`, `sandbox_mode`).
⚠️ Never copy/commit your real `~/.codex/config.toml` — it holds MCP API keys/tokens.

### Cursor
- **Global (User Rules):** Cursor stores these in the app, not a file. Paste the contents
  of `AGENTS.md` into Settings → Rules → User Rules (one-time, per machine).
- **Per project:** drop the rule file in the repo:
  ```bash
  mkdir -p <repo>/.cursor/rules && cp ~/loop-config/cursor/loop.mdc <repo>/.cursor/rules/loop.mdc
  ```
  (`alwaysApply: true` — loads in every chat. Note: `.cursorrules` is ignored in Agent mode.)

### Any other tool (Copilot, Windsurf, Cline, Amp…)
Drop `AGENTS.md` at the repo root — they read it as-is.

## Per project (once per repo)
The global manual can't know a project's commands. In each repo keep a short instructions
file (`CLAUDE.md` for Claude Code, `AGENTS.md` for the rest — symlink them to share one)
with just that project's **verify gate** (build/test/lint) and **risk tiers** (what needs
approval). Keep it under ~100 lines.

## Install on a new machine
```bash
git clone https://github.com/Parsa-29/loop-config.git ~/loop-config
# then run the per-agent steps above for whichever tools you use
```

## Updating
Edit `AGENTS.md` (and the per-tool files if needed) → commit → push. Re-run the copy step
for each agent (or use symlinks so a `git pull` updates everything at once).

## Principles (why it's built this way)
- Instruction files have a real budget (~100-150 slots; Cursor always-apply < ~2000 tokens).
  Keep the manual lean, don't duplicate it into every project file, link long detail.
- Don't restate tools the agent already auto-discovers. One rule — "reuse an existing
  skill/tool/MCP before building from scratch" — is enough.
- The only deterministic guarantees are the per-agent gates (Claude `ask`, Codex
  sandbox/approval, Cursor allowlist). Prose is guidance. Don't over-engineer the harness.
