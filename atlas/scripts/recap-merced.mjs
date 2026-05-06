import { chromium } from "playwright";
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({
  viewport: { width: 1280, height: 900 },
  userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
});
const page = await ctx.newPage();
await page.goto("https://www.mccd.edu/", { waitUntil: "load", timeout: 60000 });
await page.waitForTimeout(5000);
await page.screenshot({ path: "/Users/dayonekoo/Desktop/code/kallipolis/.claude/worktrees/peaceful-edison-6b7d19/atlas/public/brand-audit/thumbs/merced.png", clip: { x: 0, y: 0, width: 1280, height: 600 } });
await browser.close();
console.log("Re-captured merced");
