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

### 1. Read, Filter, Batch

Read `employers.json`. Build the attempt set:

- `website` key must be absent (not `null`, not present as a string)
- If a `region` argument was provided, `region ∈ employer.regions`

Entries with `website: null` are already-flagged human-review cases; skip them.
Entries with a URL are already validated; skip them. Entries in other regions
(when a region arg is set) are out of scope; skip them.

Report the attempt-set size before processing begins. Process the attempt set in
batches of 10-15 to maintain quality of web research per employer. Report
progress after each batch.

### 2. Web Research (per employer)

For each employer, conduct a focused web search:
- Search: `"{employer name}" {sector} {region} official website`
- Identify whether an **official institutional website** exists
- Distinguish official sites from directory listings (Yelp, BBB, Yellow Pages, Manta)

**CRITICAL — Verify every URL by fetching the page.** Search results frequently
surface parked domains, expired sites, and ad-stuffed placeholder pages that appear
legitimate in search snippets. Before assigning any `website` value:
- Fetch the candidate URL with WebFetch
- Confirm the page contains actual business content (company description, services,
  contact information, careers/about pages)
- Reject any domain that is parked, under construction, redirecting to ad networks,
  or serving only tracking scripts and iframes
- If the top search result is not fetchable or is parked, check the next 2-3 results
  before concluding the employer has no website

### 3. Apply Viability Criteria

Evaluate each employer against the five criteria defined in
`references/viability-criteria.md`. An employer must satisfy **all five** to be retained.

**Quick reference — the five criteria:**
1. **Institutional web presence** — Has an official website representing the organization
2. **Currently operating** — Not closed, sold, defunct, or pending closure
3. **Distinct entity** — Not a sub-department, satellite venue, or duplicate of a parent org
4. **CTE-relevant workforce** — Employs in roles that CTE programs train for
5. **Partnership capacity** — Has organizational infrastructure (HR, training, management)
   beyond a sole proprietor or micro-operation

### 4. Enrich Viable Employers

For each employer that passes validation, add a `website` field with the verified URL:
```json
{
  "name": "Kaweah Health",
  "sector": "Healthcare",
  "description": "...",
  "regions": ["CVML"],
  "occupations": ["29-1141"],
  "website": "https://www.kaweahhealth.org"
}
```

For employers under a parent organization (e.g., a clinic within a health system),
use the parent organization's website and note the relationship in the description.

### 5. Record Removals

Track every removed employer with a reason. After processing, report:
- Total employers assessed
- Employers retained (with website)
- Employers removed (with name and reason)

### 6. Write Output

Write the filtered and enriched list back to `employers.json`. Preserve the existing
JSON schema — only add the `website` field and update descriptions where needed.
Do not modify `occupations`, `regions`, or `sector` fields.

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

- Do not invent or guess URLs. Every `website` value must be verified via web search.
- Do not modify the employer's `name` field — the pipeline already cleaned names.
- Do not re-score or re-rank employers. This step is binary: viable or not.
- Do not re-attempt entries where `website` is already present (either as a URL or
  as `null`). These are durable attempt records from prior runs — a URL means
  validated, `null` means flagged for human review. Re-attempting wastes web
  calls and can silently overwrite a deliberate human flag.
- Preserve the file's JSON array structure and field ordering.

## Additional Resources

### Reference Files

- **`references/viability-criteria.md`** — Detailed viability criteria with examples,
  edge cases, and rationale for each criterion
