// Development only: npm install --no-save playwright, then run this script.
// Rasterizes the original SVG without changing the artwork. Runtime needs no npm.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
(async () => {
  const browser = await chromium.launch({headless: true});
  const page = await browser.newPage({viewport: {width: 1600, height: 900}, deviceScaleFactor: 1});
  const assets = path.resolve(__dirname, '../assets');
  await page.goto(pathToFileURL(path.join(assets, 'b1scu1tk1d-landscape.svg')).href);
  await page.screenshot({path: path.join(assets, 'b1scu1tk1d-landscape.png')});
  await page.setViewportSize({width: 512, height: 512});
  await page.goto(pathToFileURL(path.join(assets, 'codex-mark.svg')).href);
  await page.screenshot({path: path.join(assets, 'codex-mark.png'), omitBackground: true});
  await browser.close();
})();
