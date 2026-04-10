# Employer Generation

*Audience: engineers operating the data pipeline. Assumes familiarity with the [pipeline overview](./overview.md) and the [graph model](../architecture/graph-model.md).*

Employer data is the most operationally subtle layer of the Kallipolis pipeline. It is sourced from the California Employment Development Department (EDD) at the **county** level, scraped per **college**, tagged to a **Centers of Excellence (COE) region**, and merged into a **shared** `employers.json` file consumed by every college in that region. Each of those scopes matters and they do not always align.

## Source: EDD ALMIS Employer Database

Employer records come from the EDD Labor Market Information Division's ALMIS Employer Database, hosted at `labormarketinfo.edd.ca.gov`. The database is sourced from Data Axle and queryable by California county, NAICS industry code, and employee size class.

The pipeline scrapes EDD via two endpoints:

| Endpoint | Use |
|---|---|
| `empResults.aspx` | Deep search by NAICS 4-digit code with size filtering and pagination |
| `countymajorer.asp` | Top ~25 major employers per county (used for fallback overview) |

Both are ASP.NET pages, so the deep search requires `__VIEWSTATE` and `__EVENTVALIDATION` form state to apply filters and paginate. See `backend/pipeline/industry/edd_employers.py` for the parsing details.

The pipeline restricts queries to a curated set of CTE-relevant NAICS 4-digit codes — agriculture, construction, manufacturing, healthcare, IT, professional services, and others. Hospitality and government codes are partially excluded because they are not searchable by NAICS in the EDD interface. The default size filter is `G` (250+ employees), since smaller employers rarely sustain the kind of partnerships SWP funds.

## The four-level scope crosswalk

The pipeline coordinates four geographic concepts. Confusing them is the most common source of bugs.

| Level | Example | Where it comes from |
|---|---|---|
| County | `Santa Clara` | EDD scraping unit |
| OEWS metro | `San Jose-Sunnyvale-Santa Clara` | EDD's metropolitan statistical areas |
| COE region | `Bay` | Centers of Excellence regional grouping |
| College | `Foothill College` | The institution running the pipeline |

The crosswalk is defined in `backend/pipeline/industry/region_maps.py`:

- `COLLEGE_REGION_MAP` — college → primary OEWS metro(s)
- `COLLEGE_COE_REGION` — college → COE region code
- `OEWS_METRO_TO_COE` — OEWS metro → COE region code
- `METRO_COUNTIES` (in `edd_employers.py`) — OEWS metro → counties
- `COLLEGE_SEARCH_COUNTIES` — college → explicit county override (for rural colleges)

## How the pipeline runs

`generate_for_college(college_key)` orchestrates the full flow for one college. It is invoked from `pipeline/industry/generate_employers.py`.

### 1. Resolve scope
The college is looked up in `catalog_sources.json` and matched to its OEWS metro(s) via `COLLEGE_REGION_MAP`. The primary metro (`metros[0]`) is used for COE region tagging. Search counties are taken from `COLLEGE_SEARCH_COUNTIES` if defined; otherwise they default to `METRO_COUNTIES[primary_metro]`.

### 2. Scrape EDD
For each search county, the pipeline iterates the curated CTE NAICS codes and calls `deep_search()` against `empResults.aspx`. Each call applies the size filter, paginates through results, parses the HTML table, and deduplicates by `(name, city)`. Results are cached as JSON in `pipeline/industry/cache/edd_deep_<counties>.json`.

### 3. Clean and deduplicate branches
Employer names from EDD are full of abbreviations (`Hosp`, `Mfg`, `Ctr`, `Univ`). The pipeline expands them via a fixed substitution table and strips legal suffixes (`Inc`, `LLC`, `Corp`). Branches of the same employer are grouped by normalized name and the largest entry is kept.

### 4. Assign sector and SOC codes
Each employer is tagged with a human-readable sector derived from its NAICS 2-digit code. Fallback SOC codes are assigned by mapping the NAICS sector to SOC major groups (`NAICS_TO_SOC_GROUPS`) and pulling occupations from those groups that exist in the college's COE region.

The fallback is replaced when LLM cleanup runs.

### 5. LLM cleanup with Gemini
Batches of 30 employers are sent to `gemini-2.5-flash` with two tasks:
1. **Clean** the name and write a one-sentence description, or return `REMOVE` for branch duplicates, internal departments, foundations, and staffing agencies.
2. **Assign** 3-8 SOC codes from the regional occupation list, restricted to roles the employer would have on its own payroll. The prompt explicitly excludes services performed by external agencies — a hospital does not employ police officers; a resort does not employ firefighters.

Returned SOC codes are validated against the regional occupation set before being attached to the employer.

### 6. Format and merge
Cleaned employers are formatted to the `employers.json` schema:
```json
{
  "name": "Kaiser Permanente",
  "sector": "Healthcare",
  "description": "Integrated managed care consortium...",
  "regions": ["Bay"],
  "occupations": ["29-1141", "29-1171", "..."]
}
```

The new entries are merged into the shared `pipeline/industry/employers.json`. The merge function deduplicates by normalized name. When a name collides, the regions and occupation lists are unioned with the existing entry.

## The merge semantics matter

Because `employers.json` is shared across all colleges and the merge unions regions, the file accumulates state over time. Three consequences:

1. **Order of operations matters.** The first college to run `generate_for_college` for a given county seeds the employer pool from that county. Later colleges in the same COE region add to it incrementally.
2. **Region tags can grow.** When Foothill scrapes Kaiser Permanente from Santa Clara County and tags it `["Bay"]`, then later Compton College scrapes Kaiser from Los Angeles County and tags it `["LA"]`, the merged entry ends up with `regions: ["Bay", "LA"]`. A national employer accumulates regional tags as more pipelines run.
3. **The COE region is set by the college, not the county.** An employer scraped from Sonoma County by Mendocino College's pipeline gets tagged with whatever COE region Mendocino's primary metro resolves to — not necessarily the COE region Sonoma geographically belongs to.

## Why the design is intentional

A naive design would scope the scrape to "all counties in the COE region" and tag employers strictly by where they sit. Kallipolis does not do that. Search counties are defined by **commutability to the college**, not by COE region boundaries.

This is correct for a workforce tool. The question is "which employers are relevant to this college's students?" not "which employers fall inside this COE polygon?" Students commute across COE lines. Mendocino students commute to Sonoma. College of the Sequoias students commute to Fresno. Lake Tahoe students commute to El Dorado County and into Sacramento.

`COLLEGE_SEARCH_COUNTIES` makes the cross-region commutability explicit for rural colleges:

| College | Search counties | Notes |
|---|---|---|
| Lassen College | Lassen, Shasta, Tehama, Plumas | Shasta (Redding) is the regional hub |
| College of the Siskiyous | Siskiyou, Shasta | Same hub logic |
| Mendocino College | Mendocino, Lake, Humboldt, Sonoma | Sonoma is the nearest large economy |
| College of the Sequoias | Tulare, Fresno, Kings | Fresno is the adjacent metro |
| Lake Tahoe Community College | El Dorado, Placer, Alpine | Sacramento is the commutable hub |

## Loading into the graph

`generate_employers.py` produces `employers.json`. A separate script, `pipeline/industry/employers.py`, loads it into Neo4j. The loader creates one `Employer` node per record, links it to each `Region` in its `regions` array via `IN_MARKET`, and links it to each `Occupation` in its `occupations` array via `HIRES_FOR`.

```python
MERGE (e:Employer {name: $name})
MERGE (e)-[:IN_MARKET]->(r:Region)
MERGE (e)-[:HIRES_FOR]->(o:Occupation)
```

Loading is idempotent. Re-running adds new edges without duplicating existing ones.

## Caveats and known issues

- **Region tag fallback.** `OEWS_METRO_TO_COE.get(metro, metro)` falls back to the raw metro string when the metro name is not in the map. Some entries (`"North Coast"` vs `"North Coast Region"`) do not match exactly, which can produce a region tag that is not a valid COE code. Verify with the loader output.
- **`PARTNERSHIP_ALIGNMENT` is computed elsewhere.** The graph holds pre-computed `College -[:PARTNERSHIP_ALIGNMENT]-> Employer` edges that the partnership landscape API reads. No script in the repository creates these edges. They are either generated ad-hoc in Neo4j or by a script that has not been added to source control.
- **EDD scraping is fragile.** ASP.NET form state is parsed with regex. If the EDD page structure changes, the scraper fails silently. Verify with `scrape_metro` and check the cache file size.
- **Gemini cleanup requires `GEMINI_API_KEY`.** Without it, the pipeline skips LLM cleanup and uses fallback NAICS-derived SOC codes. The output is loadable but lower quality.

## Operational commands

```bash
# Generate employers for one college
python -m pipeline.industry.generate_employers --college foothill

# Use cached EDD data, do not re-scrape
python -m pipeline.industry.generate_employers --college foothill --no-scrape

# Generate for all colleges with enriched course caches
python -m pipeline.industry.generate_employers --all

# Load employers.json into Neo4j
python -m pipeline.industry.employers
```
