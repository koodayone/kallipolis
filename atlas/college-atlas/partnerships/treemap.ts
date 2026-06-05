// Squarified treemap layout. Given a list of values and a W×H box, returns one
// rect per value with area proportional to the value, packed to keep cells as
// square as possible. Shared by the SVAMP demand (occupations) and supply
// (programs) treemaps so both lenses use one layout.
export function squarify(
  values: number[], X: number, Y: number, W: number, H: number,
): { x: number; y: number; w: number; h: number }[] {
  const sum = values.reduce((a, b) => a + b, 0) || 1;
  const areas = values.map((v) => (v * W * H) / sum);
  const rects: { x: number; y: number; w: number; h: number }[] = new Array(values.length);
  let x = X, y = Y, w = W, h = H, i = 0;
  while (i < areas.length) {
    const side = Math.min(w, h), start = i;
    const row = [areas[i]]; i++;
    const worst = (r: number[]) => {
      const s = r.reduce((a, b) => a + b, 0), mx = Math.max(...r), mn = Math.min(...r), s2 = s * s, d2 = side * side;
      return Math.max((d2 * mx) / s2, s2 / (d2 * mn));
    };
    while (i < areas.length && worst([...row, areas[i]]) <= worst(row)) { row.push(areas[i]); i++; }
    const rs = row.reduce((a, b) => a + b, 0), thick = rs / side;
    if (w >= h) { let yy = y; row.forEach((a, k) => { const ch = a / thick; rects[start + k] = { x, y: yy, w: thick, h: ch }; yy += ch; }); x += thick; w -= thick; }
    else { let xx = x; row.forEach((a, k) => { const cw = a / thick; rects[start + k] = { x: xx, y, w: cw, h: thick }; xx += cw; }); y += thick; h -= thick; }
  }
  return rects;
}
