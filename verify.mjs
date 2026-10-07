import { chromium } from 'file:///C:/Users/15082/.workbuddy/binaries/node/workspace/node_modules/playwright/index.mjs';
import fs from 'fs';

const URL = 'file:///E:/WorkBuddy-WZhan-4/AI-Dev-Radar/index.html';
const shots = 'E:/WorkBuddy-WZhan-4/AI-Dev-Radar/_shots';
fs.mkdirSync(shots, { recursive: true });

const browser = await chromium.launch({ headless: true, args: ['--no-sandbox','--allow-file-access-from-files'] });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 940 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

const errs = [];
page.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text()); });
page.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));

await page.goto(URL, { waitUntil: 'load', timeout: 60000 });
await page.waitForTimeout(2500);

// 探针 1：数据是否加载
const probe = await page.evaluate(() => ({
  hasData: !!window.__RADAR__,
  changes: window.__RADAR__ ? window.__RADAR__.changes.length : 0,
  models: window.__RADAR__ ? window.__RADAR__.models.length : 0,
  dates: window.__RADAR__ ? window.__RADAR__.dates.length : 0,
  status: window.__STATUS__ ? window.__STATUS__.services.length : 0,
  navItems: document.querySelectorAll('#nav a').length,
  chgItems: document.querySelectorAll('.chg').length,
  stats: document.querySelectorAll('.stat .val').length,
  statVals: [...document.querySelectorAll('.stat .val')].map(e => e.textContent),
  sparkBars: document.querySelectorAll('.spark .b').length,
  pageTitle: document.querySelector('h2.page') ? document.querySelector('h2.page').textContent : null,
  contentLen: document.getElementById('content').innerHTML.length,
}));
console.log('PROBE dash:', JSON.stringify(probe, null, 1));

async function shot(name, full = false) {
  await page.screenshot({ path: `${shots}/${name}.png`, fullPage: full });
  console.log('shot:', name);
}

await shot('01-dash');

// 变化流
await page.click('[data-v="changes"]');
await page.waitForTimeout(900);
const p2 = await page.evaluate(() => ({
  page: document.querySelector('h2.page').textContent,
  items: document.querySelectorAll('.chg').length,
  filters: document.querySelectorAll('.filters .pill').length,
  total: (document.querySelector('.filters b') || {}).textContent,
  pager: !!document.querySelector('.pager'),
}));
console.log('PROBE changes:', JSON.stringify(p2));
await shot('02-changes');

// 高影响筛选
await page.click('[data-fl="high"]');
await page.waitForTimeout(700);
const p3 = await page.evaluate(() => ({
  items: document.querySelectorAll('.chg').length,
  allHigh: [...document.querySelectorAll('.chg')].every(e => e.classList.contains('high')),
  total: (document.querySelector('.filters b') || {}).textContent,
}));
console.log('PROBE high-filter:', JSON.stringify(p3));
await shot('03-changes-high');

// 抽屉
await page.click('.chg');
await page.waitForTimeout(800);
const p4 = await page.evaluate(() => {
  const d = document.getElementById('drawer');
  return {
    open: d.classList.contains('on'),
    title: d.querySelector('h3') ? d.querySelector('h3').textContent : null,
    verdict: d.querySelector('.verdict') ? d.querySelector('.verdict').textContent.trim().slice(0,150) : null,
    kvs: d.querySelectorAll('.kv').length,
    hasSpark: !!d.querySelector('.spark'),
    hasWatchBtn: !!d.querySelector('#dwatch'),
  };
});
console.log('PROBE drawer:', JSON.stringify(p4, null, 1));
await shot('04-drawer');
await page.keyboard.press('Escape');
await page.waitForTimeout(400);

// 价格比较
await page.click('[data-v="prices"]');
await page.waitForTimeout(1400);
const p5 = await page.evaluate(() => ({
  page: document.querySelector('h2.page').textContent,
  rows: document.querySelectorAll('#c-body tr').length,
  best: document.getElementById('c-best') ? document.getElementById('c-best').textContent.replace(/\s+/g,' ').trim().slice(0,140) : null,
  firstRow: document.querySelector('#c-body tr') ? document.querySelector('#c-body tr').textContent.replace(/\s+/g,' ').trim() : null,
}));
console.log('PROBE prices:', JSON.stringify(p5, null, 1));
await shot('05-prices');

// 改用量重算
await page.fill('#c-req', '50000');
await page.waitForTimeout(900);
const p6 = await page.evaluate(() => ({
  best: document.getElementById('c-best').textContent.replace(/\s+/g,' ').trim().slice(0,120),
}));
console.log('PROBE recalc:', JSON.stringify(p6));

// 模型库
await page.click('[data-v="models"]');
await page.waitForTimeout(1000);
const p7 = await page.evaluate(() => ({
  page: document.querySelector('h2.page').textContent,
  rows: document.querySelectorAll('tbody tr').length,
  starBtns: document.querySelectorAll('[data-w]').length,
  lede: document.querySelector('.lede').textContent,
  kinds: document.querySelectorAll('[data-fk]').length,
  firstRows: [...document.querySelectorAll('tbody tr')].slice(0,3).map(r => r.textContent.replace(/\s+/g,' ').trim().slice(0,80)),
}));
console.log('PROBE models:', JSON.stringify(p7, null, 1));
await shot('06-models');

// 只看主流厂商
await page.click('#fmajor');
await page.waitForTimeout(800);
const p7b = await page.evaluate(() => ({
  total: (document.querySelector('.filters b') || {}).textContent,
  on: document.getElementById('fmajor').classList.contains('on'),
  rows: [...document.querySelectorAll('tbody tr')].slice(0,4).map(r => r.querySelector('.nm').textContent.split('\n')[0]),
}));
console.log('PROBE major-only:', JSON.stringify(p7b, null, 1));
await shot('06b-models-major');

// 类型筛选：图像
const imgBtn = await page.$('[data-fk="image"]');
if (imgBtn) { await imgBtn.click(); await page.waitForTimeout(700); }
const p7c = await page.evaluate(() => ({
  total: (document.querySelector('.filters b') || {}).textContent,
  types: [...new Set([...document.querySelectorAll('tbody tr')].map(r => r.children[2].textContent.trim()))],
}));
console.log('PROBE kind-filter:', JSON.stringify(p7c));
await page.click('[data-fk="all"]');
await page.waitForTimeout(500);

// 关注一个模型（从模型库，测试跨数据源打通）
await page.evaluate(() => localStorage.clear());
await page.reload({ waitUntil: 'load' });
await page.waitForTimeout(2200);
await page.click('[data-v="models"]');
await page.waitForTimeout(800);
// 找一个在变化流里也存在的模型（deepseek）
await page.fill('#q', 'deepseek');
await page.waitForTimeout(900);
const targetName = await page.evaluate(() => {
  const rows = [...document.querySelectorAll('tbody tr')];
  const r = rows.find(x => x.textContent.toLowerCase().includes('deepseek v4 flash'));
  return r ? r.querySelector('.nm').textContent.split('\n')[0] : (rows[0] ? rows[0].querySelector('.nm').textContent.split('\n')[0] : null);
});
console.log('target model:', targetName);
await page.click('tbody tr [data-w]');
await page.waitForTimeout(700);
await page.click('[data-v="watch"]');
await page.waitForTimeout(900);
const p8 = await page.evaluate(() => ({
  page: document.querySelector('h2.page').textContent,
  lede: document.querySelector('.lede').textContent,
  pills: [...document.querySelectorAll('[data-uw]')].map(b => b.textContent.trim()),
  chgs: document.querySelectorAll('.chg').length,
}));
console.log('PROBE watch:', JSON.stringify(p8, null, 1));
await shot('07-watch');

// 状态
await page.click('[data-v="status"]');
await page.waitForTimeout(800);
const p9 = await page.evaluate(() => ({
  page: document.querySelector('h2.page').textContent,
  svcs: document.querySelectorAll('.svc').length,
  incs: document.querySelectorAll('.inc').length,
  text: document.querySelector('.content').textContent.replace(/\s+/g,' ').slice(0,300),
}));
console.log('PROBE status:', JSON.stringify(p9, null, 1));
await shot('08-status');

// 搜索
await page.click('[data-v="dash"]');
await page.waitForTimeout(500);
await page.fill('#q', 'deepseek');
await page.waitForTimeout(900);
const p10 = await page.evaluate(() => ({
  route: document.querySelector('h2.page').textContent,
  items: document.querySelectorAll('.chg').length,
  allMatch: [...document.querySelectorAll('.chg .mname')].every(e => e.textContent.toLowerCase().includes('deepseek')),
  total: (document.querySelector('.filters b') || {}).textContent,
}));
console.log('PROBE search:', JSON.stringify(p10));
await shot('09-search');

// 全页截图（变化流，全量）
await page.fill('#q', '');
await page.waitForTimeout(700);
await page.click('[data-v="changes"]');
await page.waitForTimeout(900);
await shot('10-changes-full', true);

console.log('--- ERRORS ---');
console.log(errs.length ? errs.join('\n') : 'none');
await browser.close();
