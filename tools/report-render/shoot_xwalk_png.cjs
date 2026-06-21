// High-DPI raster of the one un-nativeable element — the SVG crosswalk funnel —
// for embedding into the .docx (build_docx.py's add_image reads /tmp/crosswalk.png).
// Clips just the .xwrap container at deviceScaleFactor 3 (e.g. 624px box -> 1872px).
//   node shoot_xwalk_png.cjs [SRC(file-url-or-path)] [OUT.png] [selector]
const path = require('path');
const { chromium } = require(path.resolve(__dirname, '../../atlas/node_modules/playwright'));

const RESEARCH = '/Users/dayonekoo/Desktop/code/kallipolis/research/swp-strategy';
let src = process.argv[2] || `file://${RESEARCH}/svamp-pathway-49-9041-doc.html?clean`;
const out = process.argv[3] || '/tmp/crosswalk.png';
const sel = process.argv[4] || '.xwrap';
if (!src.startsWith('file:') && src.startsWith('/')) src = 'file://' + src;

(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 900, height: 1400 }, deviceScaleFactor: 3 });
  await pg.goto(src, { waitUntil: 'networkidle' });
  const el = await pg.$(sel);
  await el.screenshot({ path: out });
  const box = await el.boundingBox();
  console.log('wrote', out, '— display box w/h:', Math.round(box.width), Math.round(box.height));
  await b.close();
})();
