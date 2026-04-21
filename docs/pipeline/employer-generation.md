# Employer Generation

Employer data enters the graph at the granularity the workforce development ecosystem actually coordinates at — the Centers of Excellence region. Every college in a region shares the same employer pool, and the pool is built once per region from every county the region spans.

## The essence

Employer generation turns county-level EDD records into a region-scoped employer pool. The stage runs as a pipeline of deterministic filters around a single Gemini call: EDD scrape across every county in the COE region, pre-filter, branch dedup, Gemini cleanup against the regional occupation list, merge into the shared employer file. The output — `backend/employers/employers.json` — accumulates entries across regions; a given employer can carry multiple region tags when it genuinely operates in more than one.

## Source

Employer records come from the EDD Labor Market Information Division's ALMIS Employer Database, hosted at `labormarketinfo.edd.ca.gov`. The database is sourced from Data Axle and queryable by California county, NAICS industry code, and employee size class.

The pipeline scrapes EDD via two endpoints:

| Endpoint | Use |
|---|---|
| `empResults.aspx` | Deep search by NAICS 4-digit code with size filtering and pagination |
| `countymajorer.asp` | Top ~25 major employers per county (used for fallback overview) |

Both are ASP.NET pages, which means the deep search requires `__VIEWSTATE` and `__EVENTVALIDATION` form state to apply filters and paginate. The parsing details are in `backend/employers/edd_scrape.py`.

The pipeline restricts queries to NAICS 4-digit codes that represent at least one Strong Workforce Program priority sector. The sector framework and the NAICS composition of each sector are documented in [SWP Sector NAICS Composition](./swp-sector-naics.md); `CTE_NAICS_CODES` in `backend/employers/edd_scrape.py` is the machine-readable form. Staffing and business-support codes (NAICS 5613 and 5614) are deliberately excluded because their members place workers at other employers rather than hire onto their own payroll, so they are structurally not partnership targets. The default size filter is `F` (100+ employees), since smaller employers rarely sustain the kind of partnerships SWP funds.

For the broader institutional context on EDD as a data authority, see [Data Authorities](../domain/data-authorities.md).

## Region and county

The pipeline operates in two coordinates: the **COE region** and the **county**. The region is the unit of generation; the county is the unit of EDD scraping. Every California county belongs to exactly one COE region, and the mapping is in `COE_REGION_TO_COUNTIES` in `backend/ontology/regions.py`.

| COE region | Counties |
|---|---|
| Bay | Alameda, Contra Costa, Marin, Monterey, Napa, San Benito, San Francisco, San Mateo, Santa Clara, Santa Cruz, Solano, Sonoma |
| CVML | Alpine, Amador, Calaveras, Fresno, Inyo, Kern, Kings, Madera, Mariposa, Merced, Mono, San Joaquin, Stanislaus, Tulare, Tuolumne |
| FN | Butte, Del Norte, Glenn, Humboldt, Lake, Lassen, Mendocino, Modoc, Plumas, Shasta, Sierra, Siskiyou, Tehama, Trinity |
| GS | Colusa, El Dorado, Nevada, Placer, Sacramento, Sutter, Yolo, Yuba |
| IE/D | Riverside, San Bernardino |
| LA | Los Angeles |
| OC | Orange |
| SCC | San Luis Obispo, Santa Barbara, Ventura |
| SD/I | San Diego, Imperial |

College-to-region membership is defined in `COLLEGE_COE_REGION` in the same file. OEWS metros also appear in the ontology — they remain the authority for occupation demand data keyed by `COE_REGION_DISPLAY` — but they do not participate in employer generation.

## How the stage runs

`generate_for_region(region_code)` in `backend/employers/generate.py` orchestrates the full flow for one region. It runs in five steps.

**1. Scrape EDD.** For every county in the region, the pipeline iterates the curated CTE NAICS codes and calls `deep_search()` against `empResults.aspx`. Each call applies the size filter, paginates through results, parses the HTML table, and deduplicates by `(name, city)`. Results are cached as JSON in `backend/employers/cache/`, with filenames keyed by the COE region code and the minimum size filter — for example, `backend/employers/cache/edd_region_scc_f.json`. A subsequent run with `--no-scrape` reads the cache instead of re-hitting EDD.

**2. Pre-filter, clean, and deduplicate branches.** Before dedup, a deterministic pre-filter drops rows whose NAICS is in the never-employer set (`5613`, `5614`) and rows whose name matches the sub-unit patterns (`Dept Of`, `County Of`, `City Of`, `State Of`). Survivors then pass through an abbreviation expansion table (`Hosp` → `Hospital`, `Mfg` → `Manufacturing`, `Ctr` → `Center`, and ~40 others) and have legal suffixes stripped (`Inc`, `LLC`, `Corp`). Branches of the same employer are grouped by canonical key — lowercased, suffix-stripped, trailing-location-stripped, whitespace-collapsed — and the largest size entry is kept.

**3. Assign sector and fallback SOC codes.** Each employer is tagged with a human-readable sector derived from its NAICS 2-digit code. Fallback SOC codes are assigned by mapping the NAICS sector to SOC major groups and pulling occupations from those groups that exist in the region. The regional occupation pool is pre-filtered to career-track credentials — roles requiring "no formal credential", a high school diploma, or a graduate-level degree are excluded, since they do not represent meaningful community-college workforce-development outcomes. The fallback SOC codes are replaced when LLM cleanup runs.

**4. LLM cleanup with Gemini.** Batches of `BATCH_SIZE = 100` employers are sent to Gemini Flash with two tasks. First, clean the name and write a one-sentence description, or return `REMOVE` for branch duplicates, internal departments, foundations, and staffing agencies. Second, assign 3–8 SOC codes from the regional occupation list, restricted to roles the employer would have on its own payroll. The prompt explicitly excludes services performed by external agencies — a hospital does not employ police officers, a resort does not employ firefighters. Returned SOC codes are matched against the regional occupation set with a tolerant regex so the model can return bare codes or codes wrapped with titles in any separator format.

Each Gemini call is wrapped in a retry loop with exponential backoff (up to three attempts). A batch that exhausts retries is dropped with its employer names logged, and the operator can re-run with `--no-scrape` to retry only the failed batches. The regional occupation list — the largest and most repetitive portion of the prompt — is published to Gemini's context cache once per run and referenced by cache name on every subsequent batch, so per-batch input tokens are spent only on the 100 employer names and the response-shape directive. If cache creation fails, the pipeline falls back to inlining the occupation list in each prompt.

**5. Format and merge into `employers.json`.** Cleaned employers are formatted to the `employers.json` schema (name, sector, description, regions array, occupations array) and merged into `backend/employers/employers.json` by canonical name. When a name collides with an existing entry from a previous region run, the regions and occupation lists are unioned — a national employer genuinely operating in multiple regions ends up tagged with all of them.

For the broader treatment of where Gemini is called and what constraints apply, see [AI Integration](../architecture/ai-integration.md).

## Why region, not college

The COE region is the unit the California Community Colleges Chancellor's Office, the Strong Workforce Program, and the Centers of Excellence all coordinate at. The eight regional consortia (plus the Far North subregion split) are the institutional bodies that own employer relationships at scale, publish regional demand data, and allocate SWP investment. Generating employers at the region level makes the data model match the institution, not fight it.

It also removes a class of silent bugs the earlier per-college scope produced. Under a college-scoped design, an employer scraped from a single metro within a region would be tagged with the full region code regardless of whether the rest of the region had been scraped — every sibling college in the region saw the same partial pool, mis-labeled as complete. Region-scoped generation closes the gap by construction: the counties scraped are exactly the counties the region's label asserts.

The trade-off is commutability. A handful of rural colleges have students who realistically commute across COE boundaries for employment. Under the regional model, those students see only their home region's pool. The simplification is deliberate: consistent, defensible, and aligned with the institutional unit that actually runs regional workforce development, at the cost of some edge-case coverage. If the cost turns out to matter for a specific college, the remedy is an explicit cross-region union at query time, not a return to per-college scrape scope.

## Validation and enrichment

After the pipeline produces the merged `employers.json`, a separate validation step assesses each employer against partnership viability criteria and enriches the survivors with their official website URLs. The validation is implemented as a Claude skill, `validate-employers`, and runs as a manual step before the data is loaded into the graph.

The skill applies five viability criteria, derived from the Strong Workforce Program's partnership requirements. An employer must satisfy all five to be retained.

1. **Institutional web presence.** The organization must have an official website representing it as an institution, not just a third-party directory listing. The skill verifies each candidate URL by fetching the page and confirming it serves real business content. Parked domains, expired sites, and ad-network placeholders are common false positives in search results, which is why the fetch-and-verify step is non-negotiable.

2. **Currently operating.** The organization must be actively operating — not closed, sold, or pending shutdown. The skill searches recent news for closure indicators.

3. **Distinct entity.** The employer must be a standalone organizational entity, not a sub-unit, internal venue, or alias of another employer in the list. Internal departments of larger entities, restaurants inside casinos, and generic names that cannot be resolved to a specific organization all fail this check.

4. **CTE-relevant workforce.** The employer must hire for roles that community college CTE programs prepare students for. Farm labor contracting, sole-proprietor retail with no career ladder, and graduate-degree-only operations all fail this check.

5. **Partnership capacity.** The organization must have the institutional infrastructure (HR, management, training) to sustain a workforce development partnership. Sector-specific size thresholds guide the assessment: 25+ employees for healthcare, 100+ for manufacturing, 200+ for agriculture, 50+ for trades and professional services, with smaller thresholds where institutional capacity is inherent (government, education).

Each employer that passes all five criteria is enriched with a verified `website` field. Employers that fail any criterion are removed with their removal reason logged.

The validation step is what closes the gap between *what EDD's filters can produce* and *what the workforce development ecosystem can actually coordinate with*. The pipeline's NAICS and size filters are good at generating a candidate list, but they cannot distinguish between an employer with the institutional capacity for partnership work and one without it. Closed facilities, sub-departments mistaken for distinct entities, and small operations whose appearance in EDD does not translate to real partnership infrastructure all pass the generation filters but fail the viability criteria. Without this step, the employer pool would carry significant noise into the partnership generation flow that the product is built around.

The criteria themselves are the operational expression of the partial-by-design principle the [employers product document](../product/employers.md) describes — Kallipolis is built to coordinate with the actors the workforce development ecosystem already recognizes, and the validation step is how that recognition gets enforced employer by employer. The website enrichment is also what makes the home page property on each employer real.

The operator-facing entry point for running the full onboarding pipeline for a new college is the `onboard-college` Claude Code skill at `.claude/skills/onboard-college/SKILL.md`. That skill owns the runbook, invokes `validate-employers` automatically at the appropriate step between employer generation and employer load, and short-circuits the employer stages when the college's region has already been generated by a prior onboarding. Running `python3 -m employers.generate --region <code>` and `python3 -m employers.load` directly is still supported for testing and partial re-runs, but skips validation and is not the intended default workflow.

## Loading into the graph

`generate.py` produces `employers.json`. A separate script, `backend/employers/load.py`, loads it into Neo4j. The loader creates one `Employer` node per record, links it to each region in its `regions` array via `IN_MARKET`, and links it to each occupation in its `occupations` array via `HIRES_FOR`. Loading is idempotent: re-running adds new edges without duplicating existing ones. A companion helper, `prune_region_in_market()`, removes stale `IN_MARKET` edges when a region's employer pool is re-scraped and some prior entries no longer survive the new run.

Because colleges attach to the same region nodes via `IN_MARKET` (written by `ensure_college_region_link()` in `backend/ontology/regions.py`), every college in a region traverses to the same employer set at query time. This is the graph-level expression of the region-as-unit design: there is no per-college employer assignment, only a shared regional pool that all member colleges reach through the region node.

## Known sharp edges

Three operational caveats are worth knowing.

**EDD scraping is fragile.** ASP.NET form state is parsed with regex. If the EDD page structure changes, the parsers detect the shift by checking for sentinel markers (`empDetails.aspx`, `tableData`, `__VIEWSTATE`) and emit a loud warning when those markers are present but the row or form-state regex fails to capture. This makes regressions visible in the run log rather than silent in the cache file, but the regex itself still needs updating when EDD re-templates its pages.

**Gemini cleanup can fail partially.** Each batch retries up to three times with exponential backoff. A batch that exhausts retries is dropped — its employers do not reach `employers.json` for that run — and the failing names are logged so the operator can re-run with `--no-scrape` to retry just the failed batches. Without `GEMINI_API_KEY` at all, the pipeline skips the LLM cleanup step entirely and uses fallback NAICS-derived SOC codes. The output is loadable but lower quality, since the fallback assigns occupations based purely on industry sector mapping rather than on inference about what each specific employer actually hires for.

**The merged `employers.json` accumulates state across regions.** Because the merge unions regions and occupations on name collisions, re-running one region against an already-populated file grows entries for cross-region employers rather than replacing them. This is the intended behavior — an employer that genuinely operates in both Bay and LA legitimately accumulates both tags. A destructive rebuild requires clearing the file first rather than trusting the merge to overwrite.
