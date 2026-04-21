---
name: validate-employers
description: >
  This skill should be used when the user asks to "validate employers", "filter employer list",
  "check employer viability", "audit employers.json", "enrich employer data", or after running
  the employer generation pipeline. It evaluates each employer in employers.json against
  workforce development partnership viability criteria and enriches viable employers with
  official website URLs.
---

# Employer Partnership Validation

Validate and enrich employer data for community college workforce development partnerships.
Each employer is assessed against institutional viability criteria derived from the Strong
Workforce Program's partnership requirements. Non-viable employers are removed. Viable
employers are enriched with official website URLs.

## Context

Kallipolis connects California Community Colleges with regional employers for workforce
development partnerships (internships, apprenticeships, curriculum codesign, hiring MOUs,
advisory boards). The employer list is generated from EDD's ALMIS database by NAICS code
and employee count. This validation step filters for employers that have the institutional
capacity to sustain a partnership and enriches them with web presence data.

## Input

The employer data file: `backend/employers/employers.json`

Each employer entry:
```json
{
  "name": "Employer Name",
  "sector": "Healthcare",
  "description": "One-sentence description.",
  "regions": ["CVML"],
  "occupations": ["29-1141", "31-1014"]
}
```

### The `website` field is a three-state attempt record

The skill uses the presence and value of the `website` field as a durable record of
what has been done to each employer:

- **Key absent** — never attempted. These are the entries the skill processes.
- **Value is a URL string** — attempted, retained, viable. Do not re-attempt.
- **Value is `null`** — attempted, flagged for human review (typically a large
  employer whose official website couldn't be confirmed automatically). Do not
  re-attempt; a human decides whether to enrich or remove.

Removed entries are deleted from `employers.json` entirely, so they don't appear
in any of the three states. If a re-scrape re-introduces a previously removed
employer, it re-enters the "key absent" state and will be re-attempted — which is
correct, since circumstances (website, operating status) may have changed.

### Optional `region` argument

The skill accepts an optional argument naming a COE region code (e.g., `Bay`,
`SCC`, `IE/D`, `SD/I`, `FN`, `GS`, `LA`, `OC`, `CVML`). When provided, the skill
restricts its attempt set to employers tagged with that region. When absent, the
skill processes every employer with an absent `website` key across all regions.

The onboard-college skill always passes the college's region; ad-hoc invocations
can omit the argument to process all pending attempts.

## Process

Validation runs through `backend/employers/identify_websites.py`, which uses
Gemini with Google Search grounding to find and verify each employer's
official website. This backend is non-negotiable — do **not** validate via
per-entry WebFetch. Web searches through Gemini hit Google's index, never the
employer's server, so bot-protection failures (403s on legitimate hospital and
corporate sites) don't enter the picture. The module batches calls, retries
transient Gemini failures, and runs a parallel liveness check on every
assigned URL.

### 1. Read and filter

Read `backend/employers/employers.json`. Build the attempt set:

- `website` key must be absent (not `null`, not present as a string)
- If a `region` argument was provided, `region ∈ employer.regions`

Entries with `website: null` are already-flagged human-review cases; skip them.
Entries with a URL are already validated; skip them. Entries in other regions
(when a region arg is set) are out of scope; skip them.

Report the attempt-set size before invoking the Gemini backend. If the set is
empty, stop and report "nothing to do."

### 2. Invoke the Gemini backend

Call `identify_websites()` in a single Bash one-liner that reads the file,
filters to the attempt set, invokes the module, merges the `website` (or
`_remove` flag) back into the full list, and writes the file back. The
module's own logging reports per-batch progress; no batching or progress
reporting is needed at the skill level.

The region-display string passed to the module should be the human-readable
COE region name from `backend/ontology/regions.py::COE_REGION_DISPLAY` (e.g.,
`"Bay Area"`, `"Far North"`, `"South Central Coast"`) — this disambiguates
same-name employers in different parts of California. When no region
argument was provided, pass `"California"`.

Example one-liner shape (actual script should be equivalent):

```python
python3 -c "
import json, os, sys
sys.path.insert(0, 'backend')
from dotenv import load_dotenv
load_dotenv('.env')
from employers.identify_websites import identify_websites

REGION = None  # or a COE code like 'FN'
REGION_DISPLAY = 'Far North'  # or 'California' if REGION is None

with open('backend/employers/employers.json') as f:
    emps = json.load(f)

attempt = [e for e in emps if 'website' not in e and (REGION is None or REGION in e.get('regions', []))]
print(f'Attempt set: {len(attempt)}')

identify_websites(attempt, region_display=REGION_DISPLAY)

# The module mutates attempt entries in-place; apply _remove flags
kept = [e for e in emps if not e.get('_remove')]
for e in kept: e.pop('_remove', None)

with open('backend/employers/employers.json', 'w') as f:
    json.dump(kept, f, indent=2)

retained = sum(1 for e in attempt if isinstance(e.get('website'), str))
removed = sum(1 for e in attempt if e.get('_remove'))
print(f'Retained: {retained}, Removed: {removed}')
"
```

### 3. Report outcome

Read the log output from the module invocation. Parse the reported numbers
for retained URLs, removed entries, and liveness-check dead URLs. Present a
summary:

```
VALIDATION COMPLETE
━━━━━━━━━━━━━━━━━━
Attempt set:  113
Retained:      95 (84%)
Removed:       18 (16%) — no web presence, sub-departments, labor contractors, etc.
Dead URLs:      2 (assigned but failed liveness; removed)
```

Spot-check 5-10 retained entries — read their new `website` values from the
updated file and list them with sector tags for the operator to scan.

### 4. Viability criteria (reference for the Gemini prompt)

The Gemini prompt inside `identify_websites.py` already encodes the partnership
viability criteria — entries that fail any of the five are returned as
`REMOVE`. Criteria preserved here as reference for audit and for future
prompt revisions:

1. **Institutional web presence** — Has an official website representing the organization
2. **Currently operating** — Not closed, sold, defunct, or pending closure
3. **Distinct entity** — Not a sub-department, satellite venue, or duplicate of a parent org
4. **CTE-relevant workforce** — Employs in roles that CTE programs train for
5. **Partnership capacity** — Has organizational infrastructure (HR, training, management)
   beyond a sole proprietor or micro-operation

Detailed criteria with examples are in `references/viability-criteria.md`. If
those criteria change, update the Gemini prompt in `identify_websites.py`
correspondingly — the criteria list and the prompt are the two places where
the partnership-viability definition lives.

### 5. Parent-organization URLs

For employers under a parent organization (e.g., a clinic within a health
system, a plant under a corporate umbrella), the module returns the parent
organization's root URL or a dedicated sub-site with its own content (e.g.,
`adventisthealth.org/ukiah-valley/`). Deep facility-finder paths are
explicitly rejected by the prompt. This is the correct behavior: partnership
contact flows through the parent entity regardless of which specific facility
is listed.

## Output Format

Present a summary table after validation:

```
VALIDATION COMPLETE
━━━━━━━━━━━━━━━━━━
Assessed:  105
Retained:   78 (74%)
Removed:    27 (26%)

REMOVALS:
  Del Monte Foods — closed March 2025
  Latino Farm Labor Services — 2 employees, no website
  ...
```

## Edge Cases

- **Large employer without website** (e.g., 500+ employees): Flag for manual review
  rather than auto-removing. Set `"website": null` and note in the description why
  it was flagged. This is a durable state — future skill runs will not re-attempt
  the entry. A human must edit the record to either supply a URL or remove it.
- **Parent/child overlap**: When both a parent org and its subsidiary appear (e.g.,
  Community Medical Centers and Fresno Heart & Surgical Hospital), keep both but
  ensure the child's description references the parent relationship.
- **Government entities**: Use the official `.gov` domain. County departments share
  a county website — use the department-specific subpage where possible.
- **Education institutions**: Use `.edu` domain. School districts share a district
  site — use the school-specific subpage.

## Constraints

- Do not invent or guess URLs. Every `website` value must come from
  `identify_websites()` via Gemini + Google Search grounding.
- Do not fall back to per-entry WebFetch validation if the Gemini call fails.
  Report the failure, check `GEMINI_API_KEY`, and retry. Per-entry WebFetch
  is the mechanism this wiring exists to replace — bot-protection on major
  institutional sites makes it unreliable.
- Do not modify the employer's `name` field — the pipeline already cleaned names.
- Do not re-score or re-rank employers. This step is binary: viable or not.
- Do not re-attempt entries where `website` is already present (either as a URL or
  as `null`). These are durable attempt records from prior runs — a URL means
  validated, `null` means flagged for human review. Re-attempting wastes API
  calls and can silently overwrite a deliberate human flag.
- Preserve the file's JSON array structure and field ordering.

## Additional Resources

### Reference Files

- **`references/viability-criteria.md`** — Detailed viability criteria with examples,
  edge cases, and rationale for each criterion
