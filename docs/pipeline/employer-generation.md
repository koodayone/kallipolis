# Employer Generation

Employer data is the most operationally subtle stage in the Kallipolis pipeline. It is sourced from the California Employment Development Department at the *county* level, scraped *per college*, tagged to a *Centers of Excellence region*, and merged into a *shared* employer pool consumed by every college in that region. Each of those scopes matters and they do not always align. This document describes how the stage runs, why the design is the way it is, and what makes it different from the other pipeline stages.

## Source

Employer records come from the EDD Labor Market Information Division's ALMIS Employer Database, hosted at `labormarketinfo.edd.ca.gov`. The database is sourced from Data Axle and queryable by California county, NAICS industry code, and employee size class.

The pipeline scrapes EDD via two endpoints:

| Endpoint | Use |
|---|---|
| `empResults.aspx` | Deep search by NAICS 4-digit code with size filtering and pagination |
| `countymajorer.asp` | Top ~25 major employers per county (used for fallback overview) |

Both are ASP.NET pages, which means the deep search requires `__VIEWSTATE` and `__EVENTVALIDATION` form state to apply filters and paginate. The parsing details are in `backend/employers/edd_scrape.py`.

The pipeline restricts queries to a curated set of CTE-relevant NAICS 4-digit codes — agriculture, construction, manufacturing, healthcare, IT, professional services, and others. Hospitality and government codes are partially excluded because they are not searchable by NAICS in the EDD interface. The default size filter is `G` (250+ employees), since smaller employers rarely sustain the kind of partnerships SWP funds.

For the broader institutional context on EDD as a data authority, see [Data Authorities](../domain/data-authorities.md).

## The four-level scope crosswalk

The pipeline coordinates four geographic concepts. Confusing them is the most common source of bugs.

| Level | Example | Where it comes from |
|---|---|---|
| County | Santa Clara | EDD scraping unit |
| OEWS metro | San Jose-Sunnyvale-Santa Clara | EDD's metropolitan statistical areas |
| COE region | Bay | Centers of Excellence regional grouping |
| College | Foothill College | The institution running the pipeline |

The crosswalk is defined in `backend/ontology/regions.py`. It includes mappings from college to primary OEWS metro, college to COE region code, OEWS metro to COE region, and OEWS metro to counties. A separate `COLLEGE_SEARCH_COUNTIES` map provides explicit county overrides for rural colleges where the default metro-derived counties do not capture commutable employers.

## How the stage runs

`generate_for_college(college_key)` orchestrates the full flow for one college. It runs in six steps.

**1. Resolve scope.** The college is looked up in `catalog_sources.json` and matched to its OEWS metro via `COLLEGE_REGION_MAP`. The primary metro is used for COE region tagging. Search counties come from `COLLEGE_SEARCH_COUNTIES` if defined; otherwise they default to the counties associated with the primary metro.

**2. Scrape EDD.** For each search county, the pipeline iterates the curated CTE NAICS codes and calls `deep_search()` against `empResults.aspx`. Each call applies the size filter, paginates through results, parses the HTML table, and deduplicates by `(name, city)`. Results are cached as JSON in `pipeline/industry/cache/`.

**3. Clean and deduplicate branches.** Employer names from EDD are full of abbreviations (`Hosp`, `Mfg`, `Ctr`, `Univ`). The pipeline expands them via a fixed substitution table and strips legal suffixes (`Inc`, `LLC`, `Corp`). Branches of the same employer are grouped by normalized name and the largest entry is kept.

**4. Assign sector and SOC codes.** Each employer is tagged with a human-readable sector derived from its NAICS 2-digit code. Fallback SOC codes are assigned by mapping the NAICS sector to SOC major groups and pulling occupations from those groups that exist in the college's COE region. The fallback is replaced when LLM cleanup runs.

**5. LLM cleanup with Gemini.** Batches of 30 employers are sent to Gemini with two tasks. First, clean the name and write a one-sentence description, or return `REMOVE` for branch duplicates, internal departments, foundations, and staffing agencies. Second, assign 3-8 SOC codes from the regional occupation list, restricted to roles the employer would have on its own payroll. The prompt explicitly excludes services performed by external agencies — a hospital does not employ police officers, a resort does not employ firefighters. Returned SOC codes are validated against the regional occupation set before being attached to the employer.

For the broader treatment of where Gemini is called and what constraints apply, see [AI Integration](../architecture/ai-integration.md).

**6. Format and merge.** Cleaned employers are formatted to the `employers.json` schema (name, sector, description, regions array, occupations array) and merged into the shared `backend/employers/employers.json`. The merge function deduplicates by normalized name. When a name collides, the regions and occupation lists are unioned with the existing entry.

## Why the merge semantics matter

Because `employers.json` is shared across all colleges and the merge unions regions, the file accumulates state over time. Three consequences follow.

**Order of operations matters.** The first college to run `generate_for_college` for a given county seeds the employer pool from that county. Later colleges in the same COE region add to it incrementally rather than starting from scratch.

**Region tags can grow.** When a Bay Area college scrapes Kaiser Permanente from Santa Clara County and tags it with the Bay region, then later a Los Angeles college scrapes Kaiser from LA County and tags it with the LA region, the merged entry ends up tagged with both regions. A national employer accumulates regional tags as more pipelines run, which is correct — the same organization is genuinely active in multiple regions.

**The COE region is set by the college, not the county.** An employer scraped from Sonoma County by Mendocino College's pipeline gets tagged with whatever COE region Mendocino's primary metro resolves to, not necessarily the COE region Sonoma geographically belongs to. This is the most subtle of the merge semantics and it follows from the design choice described in the next section.

## Why the design is intentional

A naive design would scope the scrape to "all counties in the COE region" and tag employers strictly by where they sit. Kallipolis does not do that. Search counties are defined by *commutability to the college*, not by COE region boundaries.

This is correct for a workforce tool. The question the pipeline is answering is *which employers are relevant to this college's students?* not *which employers fall inside this COE polygon?* Students commute across COE boundaries. Mendocino students commute to Sonoma. College of the Sequoias students commute to Fresno. Lake Tahoe students commute through El Dorado County and into Sacramento.

`COLLEGE_SEARCH_COUNTIES` makes the cross-region commutability explicit for rural colleges where the default metro-derived counties miss a substantial fraction of the employers a student would actually consider.

| College | Search counties | Notes |
|---|---|---|
| Lassen College | Lassen, Shasta, Tehama, Plumas | Shasta (Redding) is the regional hub |
| College of the Siskiyous | Siskiyou, Shasta | Same hub logic |
| Mendocino College | Mendocino, Lake, Humboldt, Sonoma | Sonoma is the nearest large economy |
| College of the Sequoias | Tulare, Fresno, Kings | Fresno is the adjacent metro |
| Lake Tahoe Community College | El Dorado, Placer, Alpine | Sacramento is the commutable hub |

The override is the operational expression of a structural decision: the pipeline serves colleges, not regions, and the geographic scope of relevance is defined by what the college's students would realistically consider.

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

The criteria themselves are the operational expression of the partial-by-design principle the [employers product document](../product/employers.md) describes — Kallipolis is built to coordinate with the actors the workforce development ecosystem already recognizes, and the validation step is how that recognition gets enforced employer by employer. The website enrichment is also what makes the [home page property](../product/employers.md) on each employer real. The product section names the home page as the unique attributional feature that distinguishes employers from the other foundationals; the validation step is how that link gets there.

## Loading into the graph

`generate_employers.py` produces `employers.json`. A separate script, `backend/employers/load.py`, loads it into Neo4j. The loader creates one `Employer` node per record, links it to each region in its `regions` array via `IN_MARKET`, and links it to each occupation in its `occupations` array via `HIRES_FOR`. Loading is idempotent: re-running adds new edges without duplicating existing ones.

## Known sharp edges

Two operational caveats are worth knowing.

**EDD scraping is fragile.** ASP.NET form state is parsed with regex. If the EDD page structure changes, the scraper can fail silently. Verifying scraper output against expected cache file sizes is the operational discipline that catches this.

**Gemini cleanup requires an API key.** Without `GEMINI_API_KEY`, the pipeline skips the LLM cleanup step and uses fallback NAICS-derived SOC codes. The output is loadable but lower quality, since the fallback assigns occupations based purely on industry sector mapping rather than on inference about what each specific employer actually hires for.
