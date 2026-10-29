/* Optional real-browser acceptance. Install Playwright in a contributor environment.
 * Run: node scripts/ci/memory_viewer_browser.cjs /absolute/generated.html
 * Set AIKYA_CHROMIUM_EXECUTABLE when using an existing Chromium installation.
 */
const {chromium} = require('playwright');
const fs = require('fs');
const {pathToFileURL} = require('url');
const path = require('path');

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.AIKYA_CHROMIUM_EXECUTABLE ? {executablePath: process.env.AIKYA_CHROMIUM_EXECUTABLE} : {})});
  const page = await browser.newPage({viewport: {width: 1560, height: 1050}, colorScheme: 'light'});
  const checks = [], errors = [], external = [];
  const check = (name, pass) => checks.push({name, pass: Boolean(pass)});
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {if (message.type() === 'error') errors.push(message.text());});
  page.on('request', request => {if (/^https?:/.test(request.url())) external.push(request.url());});
  try {
    await page.goto(pathToFileURL(path.resolve(process.argv[2])).href);
    await page.waitForSelector('.node');
    const spanish=await page.locator('html').getAttribute('lang')==='es';
    check('Version 2 navy theme is default, including on a light OS',
      await page.locator('body').evaluate(el => getComputedStyle(el).backgroundColor) === 'rgb(12, 22, 39)');
    await page.locator('#theme').click();
    check('Light theme switches the whole canvas',
      await page.locator('body').evaluate(el => getComputedStyle(el).backgroundColor) === 'rgb(243, 247, 252)');
    check('Theme button describes the next action', await page.locator('#theme').textContent() === (spanish?'Tema oscuro':'Dark theme'));
    await page.locator('#theme').click();
    check('Theme can return to navy', await page.locator('body').evaluate(el => getComputedStyle(el).backgroundColor) === 'rgb(12, 22, 39)');
    check('Source overview accompanies the source tree', await page.locator('.sources #metrics strong').count() === 3);
    const expand=page.locator('.node.folder .expand').first();
    if(await expand.count()){await expand.focus();await expand.press('Enter');}
    const node = page.locator('.node.file').first();
    const label = await node.getAttribute('aria-label');
    await node.focus(); await node.press('Enter');
    check('Keyboard selection retains graph focus', await page.evaluate(() => document.activeElement.getAttribute('aria-label')) === label);
    check('Inspector exposes the selected source', Boolean(await page.locator('#detail-path').textContent()));
    await page.locator('[data-view=architecture]').click();
    check('Architecture lays out descendants after their parent', await page.evaluate(() => {
      const data = JSON.parse(document.querySelector('#snapshot').textContent);
      const visible = new Map([...document.querySelectorAll('.node')].map(el =>
        [el.dataset.nodeId, new DOMMatrix(getComputedStyle(el).transform).m41]));
      const edges = data.edges.filter(edge => edge.relation === 'contains' && visible.has(edge.source) && visible.has(edge.target));
      return edges.length > 0 && edges.every(edge => visible.get(edge.target) > visible.get(edge.source));
    }));
    check('Architecture never presents a fabricated execution trace', await page.locator('[data-view=flow]').count() === 0);
    await page.locator('[data-view=inventory]').click();
    check('Inventory includes navigable real sources', await page.locator('.inventory-row').count() > 0);
    check('Inventory hides the SVG and receives real row clicks', !await page.locator('#graph').isVisible());
    await page.locator('.inventory-row').first().click({timeout: 3000});
    check('Inventory row click reaches the inspector', Boolean(await page.locator('#detail-type').textContent()));
    await page.locator('#search').fill('no_such_source_fixture_928');
    check('Empty searches explain the empty result', await page.locator('#empty').isVisible() && await page.locator('.inventory-row').count() === 0);
    await page.locator('#search').fill('');
    await page.locator('[data-view=graph]').click();
    await page.locator('#motion').click();
    check('Motion can be disabled', await page.locator('body').evaluate(el => el.classList.contains('motion-off')));
    await page.emulateMedia({reducedMotion: 'reduce'});
    check('Reduced motion removes transitions', await page.locator('#canvas').evaluate(el => getComputedStyle(el).transitionDuration) === '0s');
    for (const width of [1560, 1024, 768, 390]) {
      await page.setViewportSize({width, height: 844});
      check('No horizontal overflow at ' + width + 'px', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    }
    check('No browser errors or CSP failures', errors.length === 0);
    check('Offline HTML makes no external requests', external.length === 0);
    const report = {checks, errors, external};
    if (process.env.AIKYA_BROWSER_REPORT) fs.writeFileSync(process.env.AIKYA_BROWSER_REPORT, JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
    if (checks.some(item => !item.pass)) process.exitCode = 1;
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
