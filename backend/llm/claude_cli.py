"""`claude -p` as a batch completion seam — the subscription, never API credits.

Curriculum alignment makes a few dozen structured-output calls per report. They run
through the user's Claude subscription via the Claude Code CLI, with tools disabled, no
session persistence, no settings or CLAUDE.md inheritance, and a JSON schema the CLI
validates before returning. Extended thinking is off: on extraction-shaped prompts it
costs tokens and wall-clock for no change in output.

    complete(system, user, schema, model="sonnet") -> {"data": dict|None, "raw": str,
                                                       "usage": {...}, "error": str|None}

One function, one shape. Callers check `data is None` and read `error`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.S)
_CWD = tempfile.mkdtemp(prefix="kallipolis-llm-")   # an empty cwd: nothing to inherit


def _parse_json(s: str):
    s = _FENCE.sub("", (s or "").strip())
    try:
        return json.loads(s)
    except ValueError:
        m = re.search(r"\{.*\}", s, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                return None
    return None


def _claude() -> str:
    """The CLI binary, resolved at call time: the Claude Code auto-updater swaps the
    file under the symlink, and a run that cached a stale path saw ENOENT mid-batch."""
    return shutil.which("claude") or "claude"


def complete(system: str, user: str, schema: dict, model: str = "sonnet",
             timeout: int = 300, retries: int = 2) -> dict:
    last = None
    for attempt in range(retries + 1):
        res = _once(system, user, schema, model, timeout)
        if res["data"] is not None:
            return res
        last = res
        time.sleep(3 * (attempt + 1))
    return last


def _once(system: str, user: str, schema: dict, model: str, timeout: int) -> dict:
    cmd = [_claude(), "-p", "--tools", "", "--no-session-persistence", "--setting-sources", "",
           "--model", model, "--output-format", "json", "--json-schema", json.dumps(schema),
           "--system-prompt", system, user]
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}  # subscription auth only
    env["MAX_THINKING_TOKENS"] = "0"
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=_CWD, env=env,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"data": None, "raw": "", "usage": {}, "error": f"timeout after {timeout}s"}
    except OSError as e:   # ENOENT while the binary is being replaced, and friends
        return {"data": None, "raw": "", "usage": {}, "error": f"could not launch claude: {e}"}
    try:
        j = json.loads(p.stdout)
    except ValueError:
        return {"data": None, "raw": p.stdout[:2000], "usage": {},
                "error": f"non-JSON CLI output (rc={p.returncode}): {p.stderr[:300]}"}
    u = j.get("usage") or {}
    usage = {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
             "cache_read_input_tokens": u.get("cache_read_input_tokens"),
             "model": ",".join((j.get("modelUsage") or {}).keys())}
    if j.get("is_error"):
        return {"data": None, "raw": str(j.get("result"))[:2000], "usage": usage,
                "error": str(j.get("result"))[:300]}
    data = j.get("structured_output")
    if data is None:
        data = _parse_json(str(j.get("result") or ""))
    return {"data": data, "raw": str(j.get("result") or "")[:2000], "usage": usage,
            "error": None if data is not None else "no parseable JSON in result"}
