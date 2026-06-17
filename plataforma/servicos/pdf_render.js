// Renderiza HTML -> PDF via Chromium (Playwright).
// Mesmo motor das skills do MazyOS (/carrossel, proposta, apresentação):
// abre o HTML no navegador, espera as fontes carregarem e imprime em A4.
// Uso: node pdf_render.js <entrada.html> <saida.pdf>
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [, , inFile, outFile] = process.argv;
  if (!inFile || !outFile) {
    console.error('uso: node pdf_render.js <entrada.html> <saida.pdf>');
    process.exit(2);
  }
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    const url = 'file://' + path.resolve(inFile).replace(/\\/g, '/');
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.pdf({
      path: outFile,
      format: 'A4',
      printBackground: true,
      preferCSSPageSize: true,
    });
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
