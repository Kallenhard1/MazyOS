// Gera o PDF da proposta via Chromium (Playwright).
// Uso: NODE_PATH="<pasta-com-node_modules>/node_modules" node gerar-pdf.js
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const file = 'file://' + path.resolve(__dirname, 'proposta.html').replace(/\\/g, '/');
  await page.goto(file, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  await page.pdf({
    path: path.join(__dirname, 'proposta.pdf'),
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
  });
  await browser.close();
  console.log('PDF gerado: proposta.pdf');
})();
