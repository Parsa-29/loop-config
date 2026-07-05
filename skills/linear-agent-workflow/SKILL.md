---
name: linear-agent-workflow
description: Use when coding from Linear issues, syncing task status, creating implementation plans, posting progress comments, or linking GitHub PRs.
---

# Linear Agent Workflow

Use Linear as the task context and status surface for coding work.

## When to Use

Use this skill when the user:
- Provides a Linear issue ID or project name.
- Asks what to work on next.
- Asks to sync task status, post progress, or link a GitHub PR.
- Mentions Linear-backed coding, agent task management, worktrees, branches, forks, or PR handoff.

## Workflow

1. Fetch Linear context first.
   - Read the issue or project before inspecting code when the task starts from Linear.
   - Treat title, description, comments, labels, status, linked PRs, assignee, priority, cycle, and project as task context.

2. Load repo-native project memory.
   - If present, read these files before planning implementation:
     - `docs/ai/project-passport.md`
     - `docs/ai/code-map.md`
     - `docs/ai/conventions.md`
     - `docs/ai/gotchas.md`
   - Treat these files as baseline project memory: architecture, conventions, critical rules, gotchas, and verification gates.
   - If they are missing, say so in the plan/progress comment and continue by inspecting code directly.

3. Load feature and dependency context.
   - If the issue has a parent, read the parent issue for feature-level context.
   - If the issue is blocked by other issues or depends on previous work, read those issues, their latest completion/handoff comments, and linked PRs when available.
   - Do not assume a fresh agent session remembers earlier tasks.

4. Plan before non-trivial work.
   - For multi-file, risky, or ambiguous changes, post a short implementation plan as a Linear comment.
   - Include intended files/modules, verification commands, risks, and blockers.

5. Keep status aligned.
   - Move to `In Progress` when implementation starts.
   - Move to `In Review` when a PR exists or the diff is review-ready.
   - Move to `Blocked` when credentials, approvals, CI, environment, or product decisions are missing.

6. Report completion in Linear.
   - Comment with summary, changed files, verification output, unresolved risks, and PR link if available.
   - Do not mark complete unless the requested done condition is satisfied.

## Guardrails

- Do not create or update Linear issues unless the user asked or provided an issue ID.
- Do not invent issue IDs, team names, labels, projects, statuses, or PR URLs.
- Read before write: list/fetch Linear entities before mutating them.
- If Linear tools are unavailable or auth fails, tell the user exactly what failed and continue with local work only if the task has enough context.
- Git push, deploys, DB writes/migrations, dependency additions, secret edits, and live external mutations still require human approval.

## Suggested Linear Comment Shapes

Plan comment:
```md
Plan:
- Scope: ...
- Files/modules: ...
- Verification: ...
- Risks/blockers: ...
```

Completion comment:
```md
Done:
- Summary: ...
- Changed files: ...
- Verification: ...
- PR: ...
- Remaining risks: ...
```
