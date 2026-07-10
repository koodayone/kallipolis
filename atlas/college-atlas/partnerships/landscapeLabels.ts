/**
 * Plain-English role labels for the 12 SVAMP occupations — the role name leads,
 * the SOC code rides beneath as provenance. Shared across the report and the
 * dashboard (the employer-detail SOC chips and the occupations matrix rows), so
 * the twelve roles read identically everywhere.
 */
export const ROLE_LABEL: Record<string, string> = {
  "17-3023": "Electrical & Electronic Eng. Techs",
  "17-3024": "Electro-Mech. & Mechatronics Techs",
  "17-3026": "Industrial Eng. Techs",
  "17-3027": "Mechanical Eng. Techs",
  "17-3028": "Calibration Techs",
  "17-3029": "Eng. Technologists, other",
  "49-9041": "Industrial Machinery Mechanics",
  "49-9043": "Machinery Maintenance Workers",
  "51-4041": "Machinists",
  "51-9141": "Semiconductor Processing",
  "51-9161": "CNC Tool Operators",
  "51-9162": "CNC Tool Programmers",
};

/** The occupations coverage-matrix corner label — paired with the rows below. */
export const OCC_MATRIX_CORNER = "↓ role (by demand) · → college";

/**
 * The occupations coverage-matrix ROW SET — the shared adapter between the
 * landscape payload and CoverageMatrix, consumed by BOTH the report and the
 * dashboard so the two surfaces cannot drift. It encodes three semantic
 * choices that must stay in lockstep:
 *   1. rows ranked by regional demand, descending — one well-defined regional
 *      ranking, matching the demand treemap so the highest-opportunity roles
 *      surface at the top of both panels;
 *   2. the role vocabulary (ROLE_LABEL) as the row label, falling back to the
 *      federal SOC title for any code outside the curated twelve;
 *   3. the SOC code as a "SOC "-prefixed provenance sublabel.
 * (Extracted 2026-06-07 after the dashboard's hand-rolled copy of this
 * adapter silently dropped #1 and #2.)
 */
export function occupationMatrixRows(
  cells: { soc_code: string; title: string; annual_openings: number | null }[],
): { id: string; label: string; sublabel: string; title: string }[] {
  return [...cells]
    .sort((a, b) => (b.annual_openings ?? 0) - (a.annual_openings ?? 0))
    .map((c) => ({
      id: c.soc_code,
      label: ROLE_LABEL[c.soc_code] ?? c.title,
      sublabel: `SOC ${c.soc_code}`,
      title: c.title,
    }));
}
