import { chromium } from 'file:///C:/Users/15082/.workbuddy/binaries/node/workspace/node_modules/playwright/index.mjs';
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox','--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2 });
const errs = [];
page.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text()); });
page.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
await page.goto('file:///E:/WorkBuddy-WZhan-4/AI-Dev-Radar/index.html', { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(2500);
await page.click('[data-v="status"]');
await page.waitForTimeout(1200);
const p = await page.evaluate(() => ({
  page: document.querySelector('h2.page').textContent,
  svcs: document.querySelectorAll('.svc').length,
  svcNames: [...document.querySelectorAll('.svc .nm')].map(e => e.textContent),
  svcStates: [...document.querySelectorAll('.svc .st')].map(e => e.textContent),
  stats: [...document.querySelectorAll('.stat .val')].map(e => e.textContent),
  ongoing: document.querySelectorAll('.inc').length,
  headings: [...document.querySelectorAll('.sec-h h3')].map(e => e.textContent),
}));
console.log('状态页探针:', JSON.stringify(p, null, 1));
await page.screenshot({ path: 'E:/WorkBuddy-WZhan-4/AI-Dev-Radar/_shots/11-status-new.png', fullPage: true });
console.log('ERRORS:', errs.length ? errs.join('\n') : 'none');
await browser.close();
