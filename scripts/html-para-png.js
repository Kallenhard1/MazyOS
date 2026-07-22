#!/usr/bin/env node
/**
 * html-para-png.js — renderiza um HTML como imagem PNG via Playwright/Chromium.
 * Uso:  node scripts/html-para-png.js <entrada.html> <saida.png> [largura] [altura]
 *
 * Padrão: 1080x1350 (formato post 4:5). Fontes locais via file://.
 * Reutilizável por qualquer skill que precise gerar post/carrossel em PNG.
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
  const width = parseInt(process.argv[4] || '1080', 10);
  const height = parseInt(process.argv[5] || '1350', 10);
  if (!input || !output) {
    console.error('Uso: node scripts/html-para-png.js <entrada.html> <saida.png> [largura] [altura]');
    process.exit(1);
  }
  const abs = path.resolve(input);
  if (!fs.existsSync(abs)) { console.error('Arquivo não encontrado: ' + abs); process.exit(1); }

  process.env.PLAYWRIGHT_BROWSERS_PATH =
    process.env.PLAYWRIGHT_BROWSERS_PATH || path.join(process.env.HOME, '.cache/ms-playwright');

  const { chromium } = loadPlaywright();
  const systemChromium = ['/opt/pw-browsers/chromium', process.env.CHROMIUM_PATH].filter(Boolean)
    .find((p) => fs.existsSync(p));
  const browser = await chromium.launch(systemChromium ? { executablePath: systemChromium } : {});
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  await page.goto('file://' + abs, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.screenshot({ path: path.resolve(output), fullPage: false });
  await browser.close();
  console.log('PNG gerado: ' + path.resolve(output));
})().catch((e) => { console.error('ERRO:', e.message); process.exit(1); });
