#!/usr/bin/env node
/**
 * render.js — renderiza cada .slide do carrossel.html em PNG 1080x1350.
 * Uso: node render.js
 */
const path = require('path');

const PW_CANDIDATES = [
  path.join(process.env.HOME, '.npm/_npx/e41f203b7505f1fb/node_modules/playwright'),
  'playwright',
];
function loadPlaywright() {
  for (const p of PW_CANDIDATES) { try { return require(p); } catch (_) {} }
  throw new Error('Playwright não encontrado. Rode: npx playwright install chromium');
}

process.env.PLAYWRIGHT_BROWSERS_PATH =
  process.env.PLAYWRIGHT_BROWSERS_PATH || path.join(process.env.HOME, '.cache/ms-playwright');

(async () => {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 1500 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'carrossel.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts && document.fonts.ready);

  const slides = await page.$$('.slide');
  for (let i = 0; i < slides.length; i++) {
    const out = path.join(__dirname, 'whatsapp', `post-${String(i + 1).padStart(2, '0')}.png`);
    await slides[i].screenshot({ path: out });
    console.log('OK ' + out);
  }
  await browser.close();
})().catch((e) => { console.error('ERRO:', e.message); process.exit(1); });
