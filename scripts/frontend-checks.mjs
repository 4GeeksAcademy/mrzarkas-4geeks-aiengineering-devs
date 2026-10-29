// Browser integration checks against local production servers; no data writes.
import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [toolsDir, output = '/private/tmp/healthcore-frontend-checks.json'] = process.argv.slice(2);
const { default: puppeteer } = await import(pathToFileURL(join(toolsDir,
  'puppeteer-core/lib/esm/puppeteer/puppeteer-core.js')).href);
const browser = await puppeteer.launch({ headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
const checks = [];
try {
  const page = await browser.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  for (const width of [1350, 393]) {
    await page.setViewport({ width, height: 940 });
    await page.goto('http://localhost:3000/', { waitUntil: 'networkidle0' });
    const state = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > innerWidth,
      headings: [...document.querySelectorAll('h2')].map(node => node.id),
      hrefs: [...document.querySelectorAll('article a')].map(node => node.href),
      image: document.querySelector('main img').complete && document.querySelector('main img').naturalWidth > 0,
      icon: document.querySelector('link[rel="icon"]')?.href,
    }));
    assert.equal(state.overflow, false);
    assert.deepEqual(state.headings, ['tools-title', 'about-title']);
    assert.deepEqual(state.hrefs, ['http://localhost:8080/', 'http://localhost:8080/management/']);
    assert.equal(state.image, true);
    assert.match(state.icon, /\/icon\.svg/);
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Saltar al contenido');
    checks.push(`Website ${width}px: headings, links, image, icon, no overflow, keyboard skip link PASS`);
  }

  // Only obtains a development token and performs GET requests. Never submits
  // an incident, transition, assignment or Management mutation.
  const response = await fetch('http://127.0.0.1:8000/auth/tokens', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor_id: '00000000-0000-4000-8000-000000000001', role: 'admin' }),
  });
  assert.equal(response.status, 201);
  const token = (await response.json()).access_token;
  await page.setViewport({ width: 1350, height: 940 });
  await page.goto('http://localhost:8080/#/incidents', { waitUntil: 'networkidle0' });
  await page.evaluate(value => {
    document.querySelector('#token').value = value;
    document.querySelector('#connectionForm').requestSubmit();
  }, token);
  await page.waitForSelector('#statusFilter');
  assert.equal(await page.$eval('#statusFilter', node => node.value), '');
  assert.equal(await page.$eval('#sortDirectionFilter', node => node.value), 'desc');
  const severity = await page.$eval('#severityFilter', node => node.options[1].value);
  await page.select('#severityFilter', severity);
  await page.click('.filters button[type="submit"]');
  await page.waitForFunction(value => location.hash.includes(value)
    && document.querySelector('#severityFilter')?.value === value, {}, severity);
  checks.push('Backoffice catalog filter and fixed sorting selection retained after route update PASS');

  await page.evaluate(() => { location.hash = '#/incidents/new'; });
  await page.waitForSelector('#jurisdiction_id');
  const fields = await page.evaluate(() => [...document.querySelectorAll('.create-form select')]
    .map(node => ({ id: node.id, name: node.name, required: node.required, labeled: node.labels.length > 0 })));
  assert.equal(fields.length, 7);
  assert(fields.every(field => field.required && field.name === field.id && field.labeled));
  assert.equal(await page.$eval('#clinic_id', node => node.options.length), 1);
  assert.equal(await page.$eval('#clinic_id', node => node.options[0].disabled), true);
  const jurisdiction = await page.$eval('#jurisdiction_id', node => node.options[1].value);
  await page.select('#jurisdiction_id', jurisdiction);
  await page.waitForFunction(() => document.querySelector('#clinic_id').options.length > 1);
  assert.equal(await page.$eval('#jurisdiction_id', node => node.value), jurisdiction);
  checks.push('Required creation fields remain labeled/named; choosing jurisdiction populates clinics PASS (not submitted)');
  await page.click('#disconnectButton');
  assert.equal(await page.$eval('#token', node => node.value), '');
  assert.equal(await page.$eval('#connectionForm', node => node.hidden), false);
  checks.push('Disconnect clears token and restores connection form PASS');

  await page.goto('http://localhost:8080/management/', { waitUntil: 'networkidle0' });
  assert.equal(await page.$eval('h1', node => node.textContent), 'Management');
  assert.deepEqual(pageErrors, []);
  checks.push('Management target available; no uncaught browser errors across checked pages PASS');
  await writeFile(output, JSON.stringify({ status: 'PASS', checks, dataWrites: 0 }, null, 2));
  console.log(checks.join('\n'));
} finally {
  await browser.close();
}
