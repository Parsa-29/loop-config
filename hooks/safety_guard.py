#!/usr/bin/env python3
"""Claude Code PreToolUse safety guard (loop-config).

Reads the hook payload on stdin and answers with a permission decision:
  deny - catastrophic or never-by-the-agent actions: broad rm -rf, force push to
         main/master, direct production-database access, curl | sh
  ask  - risky but sometimes legitimate: railway run/connect/shell, database
         resets, exposing a secret (.env values, private keys, Railway
         variables), edits to this guard or to Claude Code settings
Prints nothing for everything else, so the normal permission flow continues.

A guardrail, not a sandbox: an unusually spelled command can slip past it. It
fails open (allows, with a visible warning) if it crashes, so a bug here never
freezes a session. Decisions are logged without the command text, which can
hold secrets. Python 3.9+, standard library only. Tests: test_safety_guard.py.
"""

import datetime
import json
import os
import re
import shlex
import subprocess
import sys

HOME = os.path.expanduser("~")
LOG_PATH = os.environ.get("SAFETY_GUARD_LOG") or os.path.join(HOME, ".claude", "logs", "safety-guard.log")

PROTECTED_BRANCHES = {"main", "master"}
FILE_TOOLS = {"Read", "Edit", "Write", "MultiEdit", "NotebookEdit"}

REASONS = {
    "rm_broad": "recursive rm on a broad path (/, ~, a home folder or a repo root). "
                "Delete a narrower path, or give the user the command to run.",
    "force_push_protected": "force-push or delete of main/master. Push a feature branch and open a PR instead.",
    "prod_db": "connects to the production database (DATABASE_PUBLIC_URL, *.rlwy.net, prod-migrate.sh). "
               "Prod DB commands are run by the user: give them the exact command instead.",
    "curl_pipe_shell": "pipes a downloaded script into a shell. Download it, read it, and run it only with the user's OK.",
    "railway_exec": "runs a command inside a Railway environment, possibly production, with its secrets loaded.",
    "db_destructive": "resets or drops database data. Confirm the target is a local or test database.",
    "secrets": "would print or send a secret (.env values, a private key, Railway variables) or commit a .env file.",
    "guard_self": "changes the safety guard or Claude Code settings.",
}

# --- shell parsing -----------------------------------------------------------

SEPARATOR_CHARS = set("|&;()\n")
REDIRECT_OPS = {">", ">>", ">|", "&>", "&>>", "<", "<>"}
HEREDOC = re.compile(r"(?<!<)<<-?(?!<)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
WRAPPERS = {"sudo", "command", "exec", "nohup", "time", "env", "nice", "caffeinate", "xargs"}
SHELLS = {"bash", "sh", "zsh", "dash"}
INTERPRETERS = {"python", "python3", "node", "deno", "bun", "ruby", "perl", "tsx", "ts-node", "npx",
                "psql", "mysql", "sqlite3"}
SQL_CLIENTS = {"psql", "mysql", "sqlite3"}


def strip_heredocs(command):
    """Return (command without heredoc bodies, [(text before <<, body), ...])."""
    lines = command.split("\n")
    kept, bodies, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        kept.append(line)
        i += 1
        for m in HEREDOC.finditer(line):
            delim, body = m.group(2), []
            while i < len(lines) and lines[i].strip() != delim:
                body.append(lines[i])
                i += 1
            i += 1
            bodies.append((line[:m.start()], "\n".join(body)))
    return "\n".join(kept), bodies


def lex(text):
    lexer = shlex.shlex(text, posix=True, punctuation_chars="|&;()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def segments(command):
    """Split a shell command into simple commands (token lists)."""
    try:
        toks = lex(command)
    except ValueError:
        toks = command.replace("\n", " ; ").split()
    segs, cur, in_comment = [], [], False
    for t in toks:
        if t and set(t) <= SEPARATOR_CHARS:
            if cur:
                segs.append(cur)
            cur, in_comment = [], False
        elif in_comment:
            continue
        elif t.startswith("#"):
            in_comment = True
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    return segs


def command_of(toks):
    i = 0
    while i < len(toks):
        tok = toks[i]
        if ENV_ASSIGN.match(tok):
            i += 1
        elif tok in WRAPPERS:
            i += 1
            while i < len(toks) and toks[i].startswith("-"):
                i += 2 if toks[i] in ("-u", "-g", "-n") else 1
        else:
            break
    if i >= len(toks):
        return "", []
    return toks[i], toks[i + 1:]


def split_redirects(args):
    plain, targets, skip = [], [], False
    for a in args:
        if skip:
            targets.append(a)
            skip = False
        elif a in REDIRECT_OPS or (a and set(a) <= set("<>&|") and ("<" in a or ">" in a)):
            skip = True
        else:
            plain.append(a)
    return plain, targets


def base(tok):
    return os.path.basename(tok.rstrip("/")) if tok else ""


def expand(path, cwd):
    path = re.sub(r"^\$\{?HOME\}?", HOME, path)
    if path == "~" or path.startswith("~/"):
        path = HOME + path[1:]
    if not os.path.isabs(path):
        path = os.path.join(cwd or HOME, path)
    return os.path.normpath(path)


def short_flags(args):
    letters = set()
    for a in args:
        if a.startswith("-") and not a.startswith("--") and len(a) > 1:
            letters.update(a[1:])
    return letters


# --- rules: deny ---------------------------------------------------------------

PROTECTED_HOME_DIRS = {
    "Documents", "Desktop", "Downloads", "Library", "Developer", "Pictures", "Movies", "Music",
    "loop-config", ".claude", ".ssh", ".codex", ".cursor", ".agents", ".config", ".gnupg",
    ".aws", ".kube", ".docker", ".npm", ".nvm",
}
PROTECTED_ROOT_DIRS = {"Users", "System", "Library", "Applications", "usr", "etc", "var", "private", "opt", "bin", "sbin"}


def is_broad_target(target, cwd):
    raw = target.strip()
    while raw.endswith("/*"):
        raw = raw[:-2] or "/"
    if raw in ("", "/", ".", "..", "*", "~", "$HOME", "${HOME}"):
        return True
    path = expand(raw, cwd)
    if path in ("/", HOME) or path == os.path.normpath(cwd or HOME):
        return True
    if path.startswith(HOME + os.sep):
        rel = path[len(HOME) + 1:].split(os.sep)
        if len(rel) == 1 and rel[0] in PROTECTED_HOME_DIRS:
            return True
        if rel[:2] == ["Documents", "GitHub"] and len(rel) <= 3:
            return True
        return rel[0] == "Developer" and len(rel) <= 2
    parts = [p for p in path.split(os.sep) if p]
    if len(parts) <= 1:
        return True
    return len(parts) == 2 and parts[0] in PROTECTED_ROOT_DIRS and parts != ["private", "tmp"]


def rule_rm_broad(seg, cwd):
    cmd, args = command_of(seg)
    if base(cmd) != "rm":
        return False
    plain, _ = split_redirects(args)
    recursive = "--recursive" in plain or bool(short_flags(plain) & {"r", "R"})
    targets = [a for a in plain if not a.startswith("-")]
    return recursive and any(is_broad_target(t, cwd) for t in targets)


def current_branch(repo_dir):
    try:
        out = subprocess.run(["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"],
                             capture_output=True, text=True, timeout=3)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def rule_force_push(seg, cwd):
    cmd, args = command_of(seg)
    if base(cmd) != "git":
        return False
    repo_dir, i = cwd or HOME, 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            repo_dir = expand(args[i + 1], cwd)
            i += 2
        elif args[i] == "-c":
            i += 2
        else:
            i += 1
    if i >= len(args) or args[i] != "push":
        return False
    rest, _ = split_redirects(args[i + 1:])
    letters = short_flags(rest)
    force = "f" in letters or any(a in ("--force", "--force-if-includes") or a.startswith("--force-with-lease")
                                  for a in rest)
    delete = "d" in letters or "--delete" in rest
    if "--mirror" in rest:
        return True
    positional = [a for a in rest if not a.startswith("-")]
    refspecs = positional[1:]
    for ref in refspecs:
        plus = ref.startswith("+")
        spec = ref[1:] if plus else ref
        src, dst = spec.split(":", 1) if ":" in spec else (spec, spec)
        dst = dst.replace("refs/heads/", "")
        if dst in PROTECTED_BRANCHES and (force or plus or delete or (":" in spec and src == "")):
            return True
    if force and not refspecs:
        branch = current_branch(repo_dir)
        return branch is None or branch in PROTECTED_BRANCHES
    return False


PROD_MARKER = re.compile(r"DATABASE_PUBLIC_URL|\.rlwy\.net\b", re.I)
READ_ONLY_CMDS = {"grep", "egrep", "fgrep", "rg", "ag", "ack", "cat", "head", "tail", "less", "more",
                  "wc", "ls", "find", "fd", "jq"}
READ_ONLY_GIT = {"log", "diff", "show", "grep", "blame", "status"}


def rule_prod_db(seg):
    cmd, args = command_of(seg)
    b = base(cmd)
    if b.endswith("prod-migrate.sh"):
        return True
    if b in SHELLS | {"source", "."} and any("prod-migrate.sh" in a for a in args):
        return True
    if not PROD_MARKER.search(" ".join(seg)):
        return False
    if b in READ_ONLY_CMDS or (b == "git" and args[:1] and args[0] in READ_ONLY_GIT):
        return False
    if b == "sed" and not any(a.startswith("-i") or a == "--in-place" for a in args):
        return False
    return True


CURL_PIPE = [
    re.compile(r"\b(curl|wget)\b[^\n;]*\|\s*(sudo\s+(-\S+\s+)*)?(ba|z|da|k)?sh\b"),
    re.compile(r"<\(\s*(curl|wget)\b"),
    re.compile(r"\b(ba|z|da)?sh\s+(-\w+\s+)*-c\s+[\"']?\$\(\s*(curl|wget)\b"),
]


def rule_curl_pipe(command):
    return any(p.search(command) for p in CURL_PIPE)


# --- rules: ask ------------------------------------------------------------------

def rule_railway_exec(seg):
    cmd, args = command_of(seg)
    return base(cmd) == "railway" and bool(args) and args[0] in ("run", "connect", "shell", "ssh")


def rule_db_destructive(seg):
    cmd, _ = command_of(seg)
    b, low = base(cmd), " ".join(seg).lower()
    if re.search(r"\bprisma\s+migrate\s+reset\b", low):
        return True
    if re.search(r"\bprisma\s+db\s+push\b", low) and re.search(r"--(force-reset|accept-data-loss)\b", low):
        return True
    if b == "dropdb":
        return True
    if b in SQL_CLIENTS or re.search(r"\bprisma\s+db\s+execute\b", low):
        return bool(re.search(r"\b(drop\s+(database|schema|table)|truncate)\b", low))
    return False


SAFE_ENV_SUFFIXES = (".example", ".sample", ".template", ".test", ".dist", ".defaults", ".schema")
KEY_NAME = re.compile(r"id_(rsa|dsa|ecdsa|ed25519)(_sk)?|.+\.(pem|p12|pfx|keystore|jks)")
PRIVATE_KEY_BLOCK = re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")
EXPOSE_CMDS = {"cat", "head", "tail", "less", "more", "bat", "strings", "xxd", "od", "base64", "nl", "tac", "awk"}
GREP_CMDS = {"grep", "egrep", "fgrep", "rg", "ag"}
UPLOAD_CMDS = {"curl", "wget", "scp", "rsync", "nc", "gh"}


def is_env_file(path):
    m = re.fullmatch(r"\.env(\.[A-Za-z0-9_.-]+)?", base(path))
    return bool(m) and not (m.group(1) or "").lower().endswith(SAFE_ENV_SUFFIXES)


def is_key_file(path):
    return bool(KEY_NAME.fullmatch(base(path)))


def is_secret_token(tok):
    t = re.sub(r"^.*[=@]", "", tok)
    return bool(t) and (is_env_file(t) or is_key_file(t))


def has_private_key(path):
    try:
        with open(path, "rb") as f:
            return bool(PRIVATE_KEY_BLOCK.search(f.read(65536)))
    except Exception:
        return False


def grep_is_names_only(args):
    letters = short_flags(args)
    if letters & {"c", "l", "L", "q"} or any(
            a in ("--count", "--files-with-matches", "--files-without-match", "--quiet", "--silent") for a in args):
        return True
    patterns = [a for a in args if not a.startswith("-")]
    return "o" in letters and bool(patterns) and patterns[0].endswith("=")


def rule_secrets_bash(seg):
    cmd, args = command_of(seg)
    b = base(cmd)
    if b == "railway" and args[:1] == ["variables"]:
        return True
    plain, _ = split_redirects(args)
    if not any(is_secret_token(a) for a in plain):
        return False
    if b in EXPOSE_CMDS or b in UPLOAD_CMDS:
        return True
    if b in GREP_CMDS:
        return not grep_is_names_only(plain)
    if b == "sed":
        return not any(re.match(r"^s([/|#,])=", a) for a in plain)
    if b == "git":
        return args[:1] == ["add"]
    return False


GUARD_HINT = re.compile(r"loop-config/hooks|settings\.hooks\.json|settings(\.local)?\.json$")
GUARD_ANY_ARG = {"rm", "mv", "chmod", "chown", "ln", "unlink", "truncate", "tee"}
GUARD_DEST_ARG = {"cp", "rsync", "install"}


def is_guard_path(path, cwd):
    p = os.path.realpath(expand(path, cwd))
    hooks_dir = os.path.realpath(os.path.join(HOME, "loop-config", "hooks"))
    if p == hooks_dir or p.startswith(hooks_dir + os.sep):
        return True
    if p == os.path.realpath(os.path.join(HOME, "loop-config", "claude", "settings.hooks.json")):
        return True
    return bool(re.search(r"/\.claude/settings(\.local)?\.json$", p))


def rule_guard_self_bash(seg, cwd):
    if not any(GUARD_HINT.search(t) for t in seg):
        return False
    cmd, args = command_of(seg)
    b = base(cmd)
    plain, targets = split_redirects(args)

    def guard(t):
        return bool(GUARD_HINT.search(t)) and is_guard_path(t, cwd)

    if any(guard(t) for t in targets):
        return True
    paths = [a for a in plain if not a.startswith("-")]
    if b in GUARD_ANY_ARG:
        return any(guard(a) for a in paths)
    if b in GUARD_DEST_ARG:
        return bool(paths) and guard(paths[-1])
    if b == "sed" and any(a.startswith("-i") or a == "--in-place" for a in plain):
        return any(guard(a) for a in paths)
    if b == "perl" and any(re.match(r"^-\w*i", a) for a in plain):
        return any(guard(a) for a in paths)
    return False


# --- decision ------------------------------------------------------------------------

def bash_findings(command, cwd, depth=0):
    """List of (decision, rule) found in a shell command, heredoc bodies included."""
    stripped, bodies = strip_heredocs(command)
    segs = segments(stripped)
    found = []
    for seg in segs:
        if rule_rm_broad(seg, cwd):
            found.append(("deny", "rm_broad"))
        if rule_force_push(seg, cwd):
            found.append(("deny", "force_push_protected"))
        if rule_prod_db(seg):
            found.append(("deny", "prod_db"))
        if rule_guard_self_bash(seg, cwd):
            found.append(("ask", "guard_self"))
        if rule_railway_exec(seg):
            found.append(("ask", "railway_exec"))
        if rule_db_destructive(seg):
            found.append(("ask", "db_destructive"))
        if rule_secrets_bash(seg):
            found.append(("ask", "secrets"))
    if rule_curl_pipe(stripped):
        found.append(("deny", "curl_pipe_shell"))
    for prefix, body in bodies:
        prefix_segs = segments(prefix)
        b = base(command_of(prefix_segs[-1])[0]) if prefix_segs else ""
        if b in SHELLS and depth < 3:
            found.extend(bash_findings(body, cwd, depth + 1))
        elif b in INTERPRETERS or b.startswith("python"):
            if PROD_MARKER.search(body):
                found.append(("deny", "prod_db"))
            if b in SQL_CLIENTS and re.search(r"\b(drop\s+(database|schema|table)|truncate)\b", body, re.I):
                found.append(("ask", "db_destructive"))
    return found


def decide(payload):
    """Return (decision, rule, reason), or None to let the normal permission flow continue."""
    tool = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()

    if tool == "Bash":
        found = bash_findings(tool_input.get("command") or "", cwd)
    elif tool in FILE_TOOLS:
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        found = []
        if path and tool != "Read" and is_guard_path(path, cwd):
            found.append(("ask", "guard_self"))
        if path and tool == "Read" and (
                is_env_file(path) or is_key_file(path) or has_private_key(expand(path, cwd))):
            found.append(("ask", "secrets"))
    else:
        return None

    for wanted in ("deny", "ask"):
        for decision, rule in found:
            if decision == wanted:
                return decision, rule, REASONS[rule]
    return None


def log(decision, rule, payload):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        with open(LOG_PATH, "a") as f:
            f.write("%s\t%s\t%s\t%s\t%s\n" % (stamp, decision, rule, payload.get("tool_name", ""), payload.get("cwd", "")))
    except Exception:
        pass


def main():
    try:
        payload = json.loads(sys.stdin.read())
        result = decide(payload)
    except Exception as e:  # fail open, but say so
        print(json.dumps({"systemMessage": "safety-guard error, action allowed: %s" % type(e).__name__}))
        return 0
    if result is None:
        return 0
    decision, rule, reason = result
    log(decision, rule, payload)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": "safety-guard [%s]: %s" % (rule, reason),
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
