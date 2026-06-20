// Pixel-perfect PDF anchor: Chromium print-to-PDF of the report HTML (?clean).
// Vector, text-selectable, exact fidelity — the canonical reference artifact.
//   node shoot_pdf.cjs [SRC(file-url-or-path)] [OUT.pdf]
const path = require('path');
const { chromium } = require(path.resolve(__dirname, '../../atlas/node_modules/playwright'));

const RESEARCH = '/Users/dayonekoo/Desktop/code/kallipolis/research/swp-strategy';
let src = process.argv[2] || `file://${RESEARCH}/svamp-pathway-49-9041-doc.html?clean`;
const out = process.argv[3] || `${RESEARCH}/svamp-pathway-manufacturing-technician.pdf`;
if (!src.startsWith('file:') && src.startsWith('/')) src = 'file://' + src;

(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage();
  await pg.goto(src, { waitUntil: 'networkidle' });
  await pg.pdf({ path: out, printBackground: true, format: 'Letter',
                 margin: { top: '0.4in', bottom: '0.4in', left: '0.5in', right: '0.5in' } });
  await b.close();
  console.log('pdf ok ->', out);
})();
