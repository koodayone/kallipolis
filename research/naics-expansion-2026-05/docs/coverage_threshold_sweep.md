# Per-College Coverage: NAICS-matrix + pct_total filter

Tests the proposition that a pct_total ≥ 1% filter on the NAICS-matrix employer-occupation linkage produces a partnership-candidate pool that is both comprehensive (vs. LLM-curation losing CTE signal) and defensible (vs. unfiltered NAICS lighting up every regional employer).

Method: per college, compute the set of supported SOCs (reachable via PREPARES_FOR from any course at the college), then for each SOC count distinct regional employers under five linkage rules — LLM-curated, NAICS-matrix unfiltered, and the NAICS-matrix at four pct_total thresholds (0.5%, 1%, 2%, 5%).

## Headline coverage: SOCs with ≥1 candidate

| College | Region | Supp. | LLM | NAICS | ≥0.5% | ≥1% | ≥2% | ≥5% |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| College of the Desert | IE/D | 295 | 99 | 293 | 162 | 113 | 74 | 28 |
| College of the Sequoias | CVML | 314 | 68 | 309 | 127 | 90 | 57 | 23 |
| Compton College | LA | 307 | 160 | 304 | 201 | 150 | 111 | 50 |
| Foothill College | Bay | 249 | 118 | 249 | 153 | 114 | 80 | 35 |
| Irvine Valley College | OC | 253 | 121 | 252 | 163 | 123 | 86 | 37 |
| Oxnard College | SCC | 240 | 96 | 238 | 139 | 94 | 58 | 25 |
| San Diego City College | SD/I | 277 | 136 | 267 | 174 | 129 | 92 | 42 |
| Shasta College | FN | 336 | 99 | 333 | 162 | 115 | 76 | 35 |

## Coverage as % of supported SOCs

| College | LLM | ≥1% | Δ (≥1% vs LLM) |
|---|---:|---:|---:|
| College of the Desert | 33.6% | 38.3% | +4.7 pp |
| College of the Sequoias | 21.7% | 28.7% | +7.0 pp |
| Compton College | 52.1% | 48.9% | +-3.3 pp |
| Foothill College | 47.4% | 45.8% | +-1.6 pp |
| Irvine Valley College | 47.8% | 48.6% | +0.8 pp |
| Oxnard College | 40.0% | 39.2% | +-0.8 pp |
| San Diego City College | 49.1% | 46.6% | +-2.5 pp |
| Shasta College | 29.5% | 34.2% | +4.8 pp |

## Restricted to direct-CTE bands (Strong + Moderate)

Same coverage metric but restricted to SOCs whose typical entry-level education is postsecondary nondegree, associate's, high-school + on-the-job, or no formal credential — the bands where CCC training is the direct path.

| College | Direct-CTE supp. | LLM | ≥1% | LLM % | ≥1% % |
|---|---:|---:|---:|---:|---:|
| College of the Desert | 157 | 50 | 58 | 31.8% | 36.9% |
| College of the Sequoias | 180 | 38 | 53 | 21.1% | 29.4% |
| Compton College | 176 | 84 | 83 | 47.7% | 47.2% |
| Foothill College | 124 | 54 | 56 | 43.5% | 45.2% |
| Irvine Valley College | 121 | 55 | 56 | 45.5% | 46.3% |
| Oxnard College | 108 | 35 | 40 | 32.4% | 37.0% |
| San Diego City College | 151 | 73 | 64 | 48.3% | 42.4% |
| Shasta College | 202 | 65 | 75 | 32.2% | 37.1% |

## Method complementarity (full supported set)

How the LLM-curated and NAICS-matrix-≥1% sets overlap. `Both` = SOCs served by both methods. `LLM only` = SOCs with LLM-curated candidates that drop out at ≥1%. `≥1% only` = SOCs with no LLM-curated candidates that the filter recovers. The recovery delta is the proposition under test.

| College | Both | LLM only | ≥1% only | Neither |
|---|---:|---:|---:|---:|
| College of the Desert | 74 | 25 | 39 | 157 |
| College of the Sequoias | 51 | 17 | 39 | 207 |
| Compton College | 125 | 35 | 25 | 122 |
| Foothill College | 87 | 31 | 27 | 104 |
| Irvine Valley College | 95 | 26 | 28 | 104 |
| Oxnard College | 68 | 28 | 26 | 118 |
| San Diego City College | 99 | 37 | 30 | 111 |
| Shasta College | 70 | 29 | 45 | 192 |

## Per-SOC candidate count distribution at ≥1%

Distribution of the candidate-pool size per supported SOC after the ≥1% filter. The shape tells us whether SOCs end up with practical lists (handfuls of candidates) or extreme tails (either zero or hundreds).

| College | 0 | 1-5 | 6-15 | 16-50 | 51-100 | 100+ |
|---|---:|---:|---:|---:|---:|---:|
| College of the Desert | 182 | 57 | 29 | 23 | 4 | 0 |
| College of the Sequoias | 224 | 72 | 8 | 10 | 0 | 0 |
| Compton College | 157 | 58 | 34 | 42 | 12 | 4 |
| Foothill College | 135 | 41 | 22 | 30 | 16 | 5 |
| Irvine Valley College | 130 | 43 | 30 | 32 | 11 | 7 |
| Oxnard College | 146 | 40 | 20 | 30 | 2 | 2 |
| San Diego City College | 148 | 41 | 35 | 36 | 12 | 5 |
| Shasta College | 221 | 60 | 37 | 15 | 3 | 0 |

## Recovery sample: SOCs with NAICS-≥1% candidates that LLM missed

For Foothill College only — first 25 SOCs that the filter surfaces as having partnership candidates but the LLM-curated view returns zero employers for. Tests whether the recovered signal is meaningfully CTE-relevant or noise.

| SOC | Title | ≥1% candidates | Education band |
|---|---|---:|---|
| `13-1199` | Business Operations Specialists, All Other | 93 | Bachelor's |
| `43-3031` | Bookkeeping, Accounting, and Auditing Clerks | 91 | Moderate CTE |
| `43-1011` | First-Line Supervisors of Office and Administrative Support Workers | 88 | Moderate CTE |
| `11-9199` | Managers, All Other | 70 | Bachelor's |
| `15-1232` | Computer User Support Specialists | 61 | Moderate CTE |
| `43-6011` | Executive Secretaries and Executive Administrative Assistants | 25 | Moderate CTE |
| `27-2012` | Producers and Directors | 18 | Bachelor's |
| `27-3041` | Editors | 18 | Bachelor's |
| `43-6013` | Medical Secretaries and Administrative Assistants | 18 | Moderate CTE |
| `27-3023` | News Analysts, Reporters, and Journalists | 18 | Bachelor's |
| `15-1251` | Computer Programmers | 13 | Bachelor's |
| `47-2221` | Structural Iron and Steel Workers | 11 | Moderate CTE |
| `37-3011` | Landscaping and Groundskeeping Workers | 9 | Moderate CTE |
| `27-2011` | Actors | 9 | Moderate CTE |
| `29-1126` | Respiratory Therapists | 7 | Strong CTE |
| `19-1042` | Medical Scientists, Except Epidemiologists | 6 | Master's+ |
| `49-9012` | Control and Valve Installers and Repairers, Except Mechanical Door | 5 | Moderate CTE |
| `29-2099` | Health Technologists and Technicians, All Other | 4 | Strong CTE |
| `43-3051` | Payroll and Timekeeping Clerks | 4 | Moderate CTE |
| `47-2131` | Insulation Workers, Floor, Ceiling, and Wall | 3 | Moderate CTE |
| `43-9021` | Data Entry Keyers | 3 | Moderate CTE |
| `49-9099` | Installation, Maintenance, and Repair Workers, All Other | 1 | Moderate CTE |
| `29-2042` | Emergency Medical Technicians | 1 | Strong CTE |
| `29-1125` | Recreational Therapists | 1 | Bachelor's |
| `27-1011` | Art Directors | 1 | Bachelor's |
