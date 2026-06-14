# loop-config

Portable Loop Engineering working setup for Claude Code. Drop this onto any machine
to always develop in the Observe → Decide → Act → Verify → Learn loop.

## What's here
- `CLAUDE.md` — the global working method + task template + tool-reuse rule.
  Goes to `~/.claude/CLAUDE.md` (loads into **every** project on the machine).
- `settings.ask.json` — the human-approval gate (`permissions.ask`) for high-risk
  commands (push, DB migrations, deploys, publish). **Merge** into your existing
  `~/.claude/settings.json` — do not overwrite it (your `allow` list is machine-specific).

## Install on a new machine
```bash
git clone <this-repo> ~/loop-config

# 1. global working method
cp ~/loop-config/CLAUDE.md ~/.claude/CLAUDE.md

# 2. merge the approval gate into ~/.claude/settings.json (creates it if missing)
node -e '
  const fs=require("fs"), os=require("os"), path=require("path");
  const p=path.join(os.homedir(),".claude","settings.json");
  const ask=JSON.parse(fs.readFileSync(path.join(os.homedir(),"loop-config","settings.ask.json"),"utf8")).permissions.ask;
  let s={}; try{ s=JSON.parse(fs.readFileSync(p,"utf8")); }catch{}
  s.permissions=s.permissions||{};
  s.permissions.ask=Array.from(new Set([...(s.permissions.ask||[]), ...ask]));
  fs.mkdirSync(path.dirname(p),{recursive:true});
  fs.writeFileSync(p, JSON.stringify(s,null,2)+"\n");
  console.log("merged",ask.length,"ask rules");
'
```

## Per-project (do this once per repo)
The global file can't know a project's build/test commands. In each repo, keep a
`CLAUDE.md` with just that project's **verify gate** (build/test/lint commands) and
its **risk tiers** (what needs approval). Keep it under ~100 lines.

## Principles (why it's built this way)
- CLAUDE.md has a real budget (~100-150 instruction slots). Keep global lean, don't
  duplicate the loop into every project file, link long detail instead of inlining.
- Don't restate tools the agent already auto-discovers (skills/MCPs). One rule —
  "reuse an existing skill/MCP before building from scratch" — is enough.
- The only deterministic guarantee is the approval gate (and hooks). Prose is guidance.
  Don't over-engineer the harness; process discipline + a few durable files covers most.
