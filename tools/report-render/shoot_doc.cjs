// Full-page review screenshot of the editable report (no ?clean — keeps toolbar
// off via fullPage capture) for quick edit-and-show iteration. Reports page errors.
//   node shoot_doc.cjs [SRC(file-url-or-path)] [OUT.png]
const path = require('path');
const { chromium } = require(path.resolve(__dirname, '../../atlas/node_modules/playwright'));

const RESEARCH = '/Users/dayonekoo/Desktop/code/kallipolis/research/swp-strategy';
let src = process.argv[2] || `file://${RESEARCH}/svamp-pathway-49-9041-doc.html`;
const out = process.argv[3] || '/tmp/doc.png';
if (!src.startsWith('file:') && src.startsWith('/')) src = 'file://' + src;

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 872, height: 1120 }, deviceScaleFactor: 2 });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(src, { waitUntil: 'networkidle' });
  await p.waitForTimeout(250);
  await p.screenshot({ path: out, fullPage: true });
  await b.close();
  console.log('wrote', out, '| page errors:', errs.length ? errs : 'none');
})();
