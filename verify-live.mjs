import { chromium } from 'file:///C:/Users/15082/.workbuddy/binaries/node/workspace/node_modules/playwright/index.mjs';
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 940 }, deviceScaleFactor: 2 });
const errs = [];
page.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text()); });
page.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
await page.goto('https://123wersafrt.github.io/ai-dev-radar/', { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(3500);
const p = await page.evaluate(() => ({
  title: document.title,
  hasData: !!window.__RADAR__,
  changes: window.__RADAR__ ? window.__RADAR__.changes.length : 0,
  models: window.__RADAR__ ? window.__RADAR__.models.length : 0,
  pageH: document.querySelector('h2.page') ? document.querySelector('h2.page').textContent : null,
  statVals: [...document.querySelectorAll('.stat .val')].map(e => e.textContent),
  navItems: document.querySelectorAll('#nav a').length,
}));
console.log('线上探针:', JSON.stringify(p, null, 1));
await page.screenshot({ path: 'E:/WorkBuddy-WZhan-4/AI-Dev-Radar/_shots/live-01.png' });
// 切到变化流
await page.click('[data-v="changes"]');
await page.waitForTimeout(1200);
await page.screenshot({ path: 'E:/WorkBuddy-WZhan-4/AI-Dev-Radar/_shots/live-02.png' });
console.log('ERRORS:', errs.length ? errs.join('\n') : 'none');
await browser.close();
