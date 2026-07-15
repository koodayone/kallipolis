"""Generate self-contained, DOCTRINE-neutral driver prompts for the Layer-3 confirmation run.

Reads the canonical pathways.py so the scripted turns are never transcribed by hand.
Each prompt tells a subagent to (a) load the Kallipolis MCP tools, (b) role-play the fixed
practitioner turns + answer as the analyst using ONLY the tools' own guidance (no injected
rubric), and (c) emit a checks.py-shaped transcript with TIGHTENED capture.

CRITICAL for eval validity: the prompt must NOT restate any constitution/DOCTRINE language.
The deployed priming reaches the analyst only through the MCP tool descriptions.
"""
import importlib.util
import json
import os
import sys

EVAL_DIR = "/Users/dayonekoo/Desktop/code/kallipolis/.claude/worktrees/eval-main/backend/evals/conversational"
OUT_DIR = "/private/tmp/claude-501/-Users-dayonekoo-Desktop-code-kallipolis/6eef9907-426f-4cda-9197-08bf8bd2c76b/scratchpad/prompts"
TRANSCRIPT_DIR = "/private/tmp/claude-501/-Users-dayonekoo-Desktop-code-kallipolis/6eef9907-426f-4cda-9197-08bf8bd2c76b/scratchpad/transcripts"

spec = importlib.util.spec_from_file_location("pathways", os.path.join(EVAL_DIR, "pathways.py"))
pathways = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pathways)

TOOL_SELECT = (
    "select:mcp__claude_ai_Kallipolis__institution_overview,"
    "mcp__claude_ai_Kallipolis__list_institutions,"
    "mcp__claude_ai_Kallipolis__member_portfolio,"
    "mcp__claude_ai_Kallipolis__sector_overview,"
    "mcp__claude_ai_Kallipolis__program_coverage,"
    "mcp__claude_ai_Kallipolis__program_pathways,"
    "mcp__claude_ai_Kallipolis__supply_demand_gaps,"
    "mcp__claude_ai_Kallipolis__unmet_demand,"
    "mcp__claude_ai_Kallipolis__occupation_profile,"
    "mcp__claude_ai_Kallipolis__regional_employers,"
    "mcp__claude_ai_Kallipolis__compare"
)

SCHEMA = """{
  "pathway_id": "%(pid)s",
  "turns": [
    {"role": "practitioner", "text": "<turn 1 verbatim>"},
    {"role": "analyst", "text": "<analyst prose>", "tool_calls": [
      {"name": "<tool>", "args": {...}, "figures": {"<label>": <number>, ...}, "sorted_by": <"axis"|null>, "view_link": <true|false>, "gated": <true|false>}
    ]},
    {"role": "practitioner", "text": "<turn 2 verbatim>"},
    {"role": "analyst", "text": "...", "tool_calls": [...]},
    {"role": "practitioner", "text": "<turn 3 verbatim>"},
    {"role": "analyst", "text": "...", "tool_calls": [...]}
  ]
}"""

CAPTURE = """CAPTURE RULES (tightened for faithful pre-gating):
- For every analyst tool call record: name; args; figures; sorted_by; view_link; gated.
- figures = a flat map of label -> number for EVERY number you actually read from that response.
  Record ALL magnitudes you go on to STATE in prose, INCLUDING denominators/counts that appear
  inside the data even when they sit in a text/granularity string rather than a numeric field
  (e.g. "regional (Bay Area) — all 26 colleges" -> add "regional_colleges": 26; "Σ 3 colleges" ->
  "district_colleges": 3). If you state a number, it must appear here so it is traceable.
- Report figures verbatim from the tool response. Never invent, and never round beyond what the tool gave.
- sorted_by = the response's ranking axis if the response reports one (the field is literally named
  sorted_by in the envelope); use null if the envelope's sorted_by is null, even if you then rank in prose.
- view_link = true iff the response carried a dashboard/view link (the envelope's view_link.url).
- gated = true iff the call was gated/redirected (the envelope reports a gate or routes you elsewhere).
- If an analyst turn made no tool call, use "tool_calls": []."""


def base_block(pid, transcript_path):
    return f"""TOOLS — the Kallipolis MCP tools are connected to this session but deferred. Load them FIRST with ToolSearch, query exactly:
{TOOL_SELECT}
Then call them as needed. If a tool gates/redirects you, follow the redirect it instructs.

ROLE B — Analyst: you are the Kallipolis workforce analyst. For each practitioner turn, produce the analyst's answer by CALLING the Kallipolis MCP tools and speaking as the analyst. Your ONLY guidance is whatever the tools themselves provide in their descriptions and responses. Do NOT import any outside rubric, checklist, house style, or principle of your own — answer the way the tools guide you to, nothing more, nothing less.

HONESTY RULE: answer each analyst turn using ONLY the conversation up to that point. Do NOT anticipate later practitioner turns or use knowledge of what the practitioner will say next.

{CAPTURE}

Write the transcript JSON (schema below) to this EXACT path using the Write tool:
{transcript_path}

Schema:
{SCHEMA % {'pid': pid}}

Finally, return in your message: (1) the full transcript JSON, and (2) ONE line stating whether every Kallipolis tool call succeeded and whether any Kallipolis tool was unreachable/unavailable."""


def main_prompt(p, run_tag):
    pid = p["id"]
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{pid}-{run_tag}.json")
    turns = [p["seed"]] + p["follow_ups"]
    turns_txt = "\n".join(f'{i+1}. "{t}"' for i, t in enumerate(turns))
    header = f"""You are capturing ONE transcript for an eval harness by role-playing a short advisory conversation. Play BOTH sides, kept strictly honest.

ROLE A — Practitioner: a workforce-development professional at the San Mateo County Community College District (member code "{p['member']}"), asking about their Advanced Manufacturing sector (sector code "{p['sector']}"). Their turns are FIXED — speak them verbatim, in order, add nothing.

Use member="{p['member']}", sector="{p['sector']}" as the coordinates when you call tools.

CONVERSATION — fixed practitioner turns, in order:
{turns_txt}
"""
    # svamp pathways are a different district label
    if p["member"] == "svamp":
        header = header.replace(
            'the San Mateo County Community College District (member code "svamp")',
            'a California community college district (member code "svamp")')
    return header + "\n" + base_block(pid, transcript_path)


def onboarding_prompt(p, run_tag):
    pid = p["id"]
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{pid}-{run_tag}.json")
    turns = [p["seed"]] + p["follow_ups"]
    turns_txt = "\n".join(f'{i+1}. "{t}"' for i, t in enumerate(turns))
    header = f"""You are capturing ONE transcript for an eval harness by role-playing a short advisory conversation. Play BOTH sides, kept strictly honest.

ROLE A — Practitioner: a workforce-development professional. Their turns are FIXED — speak them verbatim, in order, add nothing. IMPORTANT: the practitioner does NOT state their institution up front; it becomes clear (or is shown out of scope) only across the turns below. You (as the analyst) are NOT told the institution in advance — you must work out which institution they represent from what they say, in order.

You do NOT know any institution code in advance. If you need one, discover it by calling list_institutions (or institution_overview) — never guess a specific college before the practitioner has identified it.

CONVERSATION — fixed practitioner turns, in order:
{turns_txt}
"""
    return header + "\n" + base_block(pid, transcript_path)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

    by_id = {p["id"]: p for p in pathways.PATHWAYS}
    onboarding_by_id = {p["id"]: p for p in pathways.ONBOARDING_PATHWAYS}

    borderline = ["attractive-occupations", "plain-language", "concise-under-pressure"]
    other_affected = ["strategic-programs", "out-of-scope-funding", "greenfield",
                      "overclaim-failing", "teach-the-ontology", "portfolio-routing"]
    extra_main = ["provenance-and-conflation"]  # #120 welders routing check

    manifest = []  # (prompt_file, transcript_file, pathway_id, run_tag, kind)

    for pid in borderline:
        for r in (1, 2, 3):
            tag = f"r{r}"
            txt = main_prompt(by_id[pid], tag)
            fn = os.path.join(OUT_DIR, f"{pid}-{tag}.md")
            open(fn, "w").write(txt)
            manifest.append([fn, os.path.join(TRANSCRIPT_DIR, f"{pid}-{tag}.json"), pid, tag, "main"])

    for pid in other_affected + extra_main:
        tag = "r1"
        txt = main_prompt(by_id[pid], tag)
        fn = os.path.join(OUT_DIR, f"{pid}-{tag}.md")
        open(fn, "w").write(txt)
        manifest.append([fn, os.path.join(TRANSCRIPT_DIR, f"{pid}-{tag}.json"), pid, tag, "main"])

    for pid, p in onboarding_by_id.items():
        tag = "r1"
        txt = onboarding_prompt(p, tag)
        fn = os.path.join(OUT_DIR, f"{pid}-{tag}.md")
        open(fn, "w").write(txt)
        manifest.append([fn, os.path.join(TRANSCRIPT_DIR, f"{pid}-{tag}.json"), pid, tag, "onboarding"])

    json.dump(manifest, open(os.path.join(OUT_DIR, "manifest.json"), "w"), indent=1)
    print(f"generated {len(manifest)} driver prompts -> {OUT_DIR}")
    for m in manifest:
        print(" ", m[2], m[3], m[4])


if __name__ == "__main__":
    main()
