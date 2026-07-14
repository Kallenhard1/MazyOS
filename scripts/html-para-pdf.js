#!/usr/bin/env node
/**
 * html-para-pdf.js — converte um HTML print (A4) em PDF via Playwright/Chromium.
 * Uso:  node scripts/html-para-pdf.js <entrada.html> <saida.pdf>
 *
 * O HTML deve usar @page { size:A4 } e .page com page-break-after.
 * Fontes locais (@font-face com url relativa) são resolvidas via file://.
 * Reutilizável por qualquer skill que precise gerar PDF a partir de HTML.
 */
const path = require('path');
const fs = require('fs');

const PW_CANDIDATES = [
  path.join(process.env.HOME, '.npm/_npx/e41f203b7505f1fb/node_modules/playwright'),
  'playwright',
];
function loadPlaywright() {
  for (const p of PW_CANDIDATES) { try { return require(p); } catch (_) {} }
  throw new Error('Playwright não encontrado. Rode: npx playwright install chromium');
}

(async () => {
  const input = process.argv[2];
  const output = process.argv[3];
  if (!input || !output) {
    console.error('Uso: node scripts/html-para-pdf.js <entrada.html> <saida.pdf>');
    process.exit(1);
  }
  const abs = path.resolve(input);
  if (!fs.existsSync(abs)) { console.error('Arquivo não encontrado: ' + abs); process.exit(1); }

  process.env.PLAYWRIGHT_BROWSERS_PATH =
    process.env.PLAYWRIGHT_BROWSERS_PATH || path.join(process.env.HOME, '.cache/ms-playwright');

  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + abs, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.emulateMedia({ media: 'print' });
  await page.pdf({
    path: path.resolve(output),
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' },
  });
  await browser.close();
  console.log('PDF gerado: ' + path.resolve(output));
})().catch((e) => { console.error('ERRO:', e.message); process.exit(1); });
