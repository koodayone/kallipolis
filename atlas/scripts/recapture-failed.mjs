import { chromium } from "playwright";
import path from "node:path";

const ATLAS = "/Users/dayonekoo/Desktop/code/kallipolis/.claude/worktrees/peaceful-edison-6b7d19/atlas";

const targets = [
  { id: "butte",        url: "https://www.butte.edu/",        wait: 5000 },
  { id: "reedley",      url: "https://www.reedleycollege.edu/", wait: 5000 },
];

const browser = await chromium.launch({ headless: true });
for (const t of targets) {
  let attempt = 0;
  const maxA = t.retries ?? 1;
  while (attempt < maxA) {
    attempt++;
    const ctx = await browser.newContext({
      viewport: { width: 1280, height: 900 },
      userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    });
    const page = await ctx.newPage();
    try {
      const r = await page.goto(t.url, { waitUntil: "load", timeout: 60_000 });
      await page.waitForTimeout(t.wait);
      await page.screenshot({
        path: path.join(ATLAS, "public", "brand-audit", "thumbs", `${t.id}.png`),
        clip: { x: 0, y: 0, width: 1280, height: 600 },
      });
      console.log(`✓ ${t.id} (HTTP ${r ? r.status() : "?"}, attempt ${attempt})`);
      await ctx.close();
      break;
    } catch (e) {
      console.log(`✗ ${t.id} attempt ${attempt}: ${e.message}`);
      await ctx.close();
      if (attempt < maxA) await new Promise(r => setTimeout(r, 3000));
    }
  }
}
await browser.close();
