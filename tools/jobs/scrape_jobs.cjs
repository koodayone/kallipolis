// Live job postings for a SOC from the PUBLIC CareerOneStop job search
// (careeronestop.org/Toolkit/Jobs) — free, public, no login, no API key, no NLx
// agreement. The gated CareerOneStop *Jobs API* requires NLx; this is the public
// website the same data is served through, read with a real browser (the listings
// are JS-rendered, so a plain fetch returns an empty shell — hence Playwright).
//
// Usage:  node scrape_jobs.cjs <soc> <zip> [radius]   →  JSON array on stdout
//   [{ soc, title, employer, location, date, url }, ...]
//
// The find-live-postings skill consumes this and makes the semantic judgment
// (employer recognizability × title↔role similarity); this script is just the
// reliable, structured acquisition layer.
const { chromium } = require('/Users/dayonekoo/Desktop/code/kallipolis/atlas/node_modules/playwright');

const soc = process.argv[2] || '17-3026';
const zip = process.argv[3] || '94022';
const radius = process.argv[4] || '25';
const keyword = soc.includes('.') ? soc : `${soc}.00`;
const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
           '(KHTML, like Gecko) Chrome/124.0 Safari/537.36';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ userAgent: UA });
  const url = `https://www.careeronestop.org/Toolkit/Jobs/find-jobs.aspx` +
              `?keyword=${keyword}&location=${zip}&radius=${radius}`;
  await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(3500);

  const jobs = await page.evaluate((soc) => {
    const DATE = /\d{2}\/\d{2}\/\d{4}/;
    const LOC = /[A-Z][A-Za-z.\s]+,\s*[A-Z]{2}\b/;
    const seen = new Set();
    const out = [];
    for (const a of document.querySelectorAll('a[href*="find-jobs-details"]')) {
      // climb to the card that holds the whole row (title + company + loc + date)
      let card = a.closest('li, tr, div');
      for (let i = 0; i < 5 && card && !DATE.test(card.innerText || ''); i++) card = card.parentElement;
      if (!card) continue;
      const title = a.textContent.trim();
      const cells = (card.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean);
      const date = cells.find((c) => DATE.test(c)) || '';
      const location = cells.find((c) => LOC.test(c) && /,\s*[A-Z]{2}$/.test(c)) || '';
      const employer = cells.find((c) =>
        c !== title && c !== location && c !== date && c !== 'Federal Contractor' && c.length > 1) || '';
      const href = a.getAttribute('href');
      const url = href.startsWith('http') ? href : 'https://www.careeronestop.org' + href;
      if (seen.has(url)) continue;
      seen.add(url);
      out.push({ soc, title, employer, location, date, url });
    }
    return out;
  }, soc);

  process.stdout.write(JSON.stringify(jobs));
  await browser.close();
})();
