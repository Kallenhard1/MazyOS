// Gera os PDFs (apresentação + proposta) da versão "só site" (sem GMB) via Chromium (Playwright).
// Uso: NODE_PATH="<pasta-com-node_modules>/node_modules" node gerar-pdf.js
const { chromium } = require('playwright');
const path = require('path');

const ALVOS = [
  ['apresentacao.html', 'Apresentacao-Fryda-Site.pdf'],
  ['proposta.html', 'Proposta-Fryda-Site.pdf'],
];

(async () => {
  const browser = await chromium.launch();
  for (const [html, pdf] of ALVOS) {
    const page = await browser.newPage();
    const file = 'file://' + path.resolve(__dirname, html).replace(/\\/g, '/');
    await page.goto(file, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.pdf({
      path: path.join(__dirname, pdf),
      format: 'A4',
      printBackground: true,
      preferCSSPageSize: true,
    });
    await page.close();
    console.log('PDF gerado: ' + pdf);
  }
  await browser.close();
})();
