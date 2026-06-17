const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  const file = 'file://' + path.resolve(__dirname, 'carrossel.html').replace(/\\/g, '/');
  await page.goto(file, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);
  const slides = await page.$$('.slide');
  for (let i = 0; i < slides.length; i++) {
    const n = String(i + 1).padStart(2, '0');
    await slides[i].screenshot({ path: path.join(__dirname, 'instagram', `slide-${n}.png`) });
    console.log(`slide-${n}.png  ok`);
  }
  await browser.close();
  console.log(`\n${slides.length} slides renderizados`);
})();
