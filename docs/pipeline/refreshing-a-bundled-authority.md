# Refreshing a Bundled Authority

Several of the graph's facts come from files an institutional authority publishes and Kallipolis bundles in the repository: the Centers of Excellence occupational demand table, the COE projected-supply table, the Curriculum Inventory export, the MIT living-wage table. Each is republished on the authority's own cadence, and each is copied downstream — into generated files, into the graph, into evaluation fixtures, and into figures people wrote into report definitions. A refresh that updates the source and some of the copies leaves the product quoting two editions at once. This document is the procedure that prevents that, written for the COE demand table and applicable, with the artifact list changed, to the others.

## The essence

A bundled authority is copied at four levels, and a refresh has to reach all four in dependency order. The first three regenerate from the file: derived files committed to git, the graph, the running backend's caches. The fourth does not: the openings figures a person wrote into a demand note, a skill's worked example, a test corpus captured from a live graph. Every copy either states its vintage or can be compared by value, and `scripts/check_demand_vintage.py` does both, so "did we update everything" is a command rather than a question.

## The copies

| Level | Artifact | How it refreshes |
|---|---|---|
| Source | `backend/ontology/occupational_demand_middle_skill.csv` | replaced by the new export |
| Derived, committed | `backend/occupations/occupations.json` and its sidecar `backend/occupations/occupations.meta.json` | `python -m occupations.generate` |
| Derived, committed | `backend/partnerships/data/sector_socs.csv` | `python scripts/generate_sector_socs.py` |
| Graph | every `Region`-`DEMANDS`-`Occupation` edge, stamped with the vintage | `python -m pipeline.reload`, locally and then on the production database |
| In-process | the parsed table, the crosswalk gate, every `lru_cache`, the warmed landscape index | backend restart |
| Evaluation corpora, committed | `backend/evals/seed.json.gz`, `backend/evals/goldens/`, `backend/evals/char_surfaces/` | `python -m evals.extract_seed`, `python -m evals.characterization`, `python -m evals.characterization_surfaces`, against the reloaded graph |
| Authored | openings figures in the report definitions under `backend/partnerships/saved_reports/` (their demand notes); the worked example in the evaluate-program skill | a person, re-reading each against the new table |

Two design choices make the chain checkable. The export's columns are resolved from its header by pattern (`ontology.supply.coe_demand_columns`), because each release renames the year-bearing columns and a reader that named them produced nulls without an error; a column no pattern matches now stops the run. And the derived copies state their edition: the generated file's sidecar names the export and vintage it came from, and the loader stamps the same vintage on every `DEMANDS` edge, so a generated file or a graph that lags the bundled export is detectable without comparing values.

## The procedure

1. **Obtain the export.** The COE lookup dashboards require a signed-in Google session; export the table with the middle-skill filter applied and every region selected, so the COE's own designation defines the universe. Expect the same shape as the bundled file: one row per region per occupation, the statewide `CA` rollup included.
2. **Compare before swapping.** Diff the universe (SOCs added or dropped, per region), the distribution of openings and wage changes, and the rows the shipped reports depend on. A universe change means the sector map (`backend/partnerships/data/coe_occupation_sector.csv`) may need a manual entry for a new occupation before the join will regenerate. Run the check before and after the swap and compare its regional-totals line: the nine regions partition the state's counties, so their jobs should sum to about the `CA` row, and a region whose total jumps while the statewide row barely moves has changed its county coverage. A regional anomaly is worth a note to the authority before it is treated as real.
3. **Swap the file** and run `python scripts/check_demand_vintage.py`. Every derived copy should now disagree with the export, by vintage or by value. That is the list of work.
4. **Regenerate the derived files**: the universe, then the sector join. Confirm the generated universe's SOC count and the sidecar's vintage.
5. **Reload the graph locally**, restart the backend, and run the check with `--graph`: edge values and the vintage stamp should agree with the export.
6. **Regenerate the evaluation corpora** against the reloaded graph: the seed, the goldens, the characterization surfaces. Splice rather than re-extract where a corpus carries content unrelated to the refreshed authority.
7. **Re-author the human copies.** The check names each report definition whose demand note quotes a figure the new table does not support, and the skill's worked example. Rewrite them, and reissue the affected reports as a dated edition.
8. **Run the check once more, without and with `--graph`, until it reports no disagreement.** Then take the graph to production with the database push and deploy the backend.

## What the check reads

`backend/ontology/demand_vintage.py` compares each copy with the export: the nine regions' totals against the statewide row, reported for comparison across releases rather than as a failure; the sidecar's vintage; every value in the generated universe; the sector join's SOC set; every `DEMANDS` row and occupation title in the eval seed; the vintage literal embedded in each characterization surface; each report definition's authored openings figures against the export's values for that definition's occupations in the member's region, or their sum; the skill's worked example against the Bay row it quotes; and, with `--graph`, every edge's four values and its vintage stamp, plus the occupation count. The file-level checks also run under pytest, so a partial refresh fails CI.

## The same shape elsewhere

The COE projected-supply table (`backend/ontology/supply_by_top.csv`) and the Curriculum Inventory export (`backend/ontology/coci.py`) are bundled the same way and carry their vintage the same way, in the file's own header or a stated snapshot date. Their copies are fewer — neither is materialized into the graph as a measure — so their refresh is the swap, the vintage constant, and the reports that quote them.
