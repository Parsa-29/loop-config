---
name: project-brain
description: Bootstrap or update repo-native project memory in docs/ai/project-brain.md so fresh agents can understand a project before planning or coding. Use for /plantask, multi-file changes, ambiguous tasks, or when Project Brain is missing and project context matters.
---

# project-brain — repo-native project memory

Use this skill to create or refresh the small project-memory file that every fresh agent can
read before planning or coding.

## Core idea

`docs/ai/project-brain.md` is the fast baseline. It should orient an agent in a few minutes:
what the project is, where important code lives, what commands verify work, and what gotchas
matter. It is not a full wiki.

Expanded projects may also keep:
- `docs/ai/project-passport.md`
- `docs/ai/code-map.md`
- `docs/ai/conventions.md`
- `docs/ai/gotchas.md`
- `docs/ai/decisions/`

The one-file brain comes first; split into expanded files only when the single file grows too
large or the project needs more structure.

## When to bootstrap automatically

If `docs/ai/project-brain.md` is missing, bootstrap it before planning when:
- the user runs `/plantask`;
- the work will create multiple Linear tasks;
- the task spans multiple modules or frontend/backend/data boundaries;
- the task is ambiguous and project orientation affects the plan;
- the agent cannot confidently locate the relevant code;
- the user asks about project memory/context or making agents understand the project.

Do not auto-bootstrap for:
- a tiny one-file fix where the relevant code is obvious;
- read-only questions;
- tasks that explicitly say not to touch docs;
- repos where writes are unavailable.

If you skip bootstrap, mention briefly that Project Brain is missing and why you skipped it.

## How to bootstrap

Inspect only high-signal repo context. Keep it fast:
1. Project instructions: `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/*` when present.
2. Human docs: `README*`, `docs/` index files.
3. Package/config files: `package.json`, lockfiles, `pyproject.toml`, `Cargo.toml`,
   `go.mod`, framework configs, test configs.
4. Top-level app/source directories and route/API entry points.
5. Existing tests and scripts that reveal verification commands.

Create `docs/ai/project-brain.md` using `templates/project-brain/project-brain.md` as the
shape. Fill only facts supported by repo evidence. Mark unknowns explicitly.

Every generated file MUST include this warning near the top:

```md
> DRAFT: generated from repository inspection.
> Code is the source of truth. If this file conflicts with code, update this file.
```

## What not to do

- Do not invent product purpose, architecture, services, or commands.
- Do not paste secrets or `.env` values.
- Do not dump a full file tree.
- Do not duplicate generic framework docs.
- Do not block urgent narrow fixes just to create memory.

## Updating existing Project Brain

When `docs/ai/project-brain.md` exists:
- read it before planning substantial work;
- verify important claims against code when they matter;
- if you discover a non-obvious project fact, gotcha, or changed verification command, update it;
- if code disagrees with memory, trust code and either update the memory or call out the drift.

## Commit guidance

For coding work, keep Project Brain bootstrap/update as its own logical commit when practical:

```bash
git add docs/ai/project-brain.md
git commit -m "docs: bootstrap project brain"
```

Then commit implementation separately. If the change is documentation-only or `/plantask`
setup-only, one commit is fine.
