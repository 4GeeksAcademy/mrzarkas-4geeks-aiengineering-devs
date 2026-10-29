// Temporary tools live outside the app: Lighthouse 12.8.2 and its puppeteer-core.
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const toolDir = process.env.AUDIT_TOOLS_DIR || process.argv[6];
if (!toolDir) throw new Error('Set AUDIT_TOOLS_DIR to the temporary node_modules directory.');
const load = path => import(pathToFileURL(join(toolDir, path)).href);
const { default: puppeteer } = await load('puppeteer-core/lib/esm/puppeteer/puppeteer-core.js');
const { navigation } = await load('lighthouse/core/index.js');
const { default: desktop } = await load('lighthouse/core/config/desktop-config.js');
const { ReportGenerator } = await load('lighthouse/report/generator/report-generator.js');
const [outputDir, target = 'website', mode = 'desktop', count = '3'] = process.argv.slice(2);
if (!outputDir || !['website', 'backoffice', 'summary'].includes(target)
  || !['desktop', 'mobile'].includes(mode) || !/^[1-3]$/.test(count)) {
  throw new Error('Usage: node scripts/frontend-audit.mjs OUTPUT website|backoffice|summary desktop|mobile [1-3]');
}
await mkdir(outputDir, { recursive: true });
const url = target === 'website' ? 'http://localhost:3000/'
  : `http://localhost:8080/#/${target === 'summary' ? 'summary' : 'incidents'}`;
const config = mode === 'desktop' ? desktop : { extends: 'lighthouse:default' };
let token;
// Chrome traces can include evaluated script arguments; redact the ephemeral
// credential before any artifact is written, including embedded script text.
const redact = value => token ? value.replaceAll(token, '[REDACTED_DEVELOPMENT_JWT]') : value;
if (target === 'summary') {
  // Development token is ephemeral: never written to disk or report URLs.
  const response = await fetch('http://127.0.0.1:8000/auth/tokens', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor_id: '00000000-0000-4000-8000-000000000001', role: 'direction' }),
  });
  if (!response.ok) throw new Error(`Development token unavailable: HTTP ${response.status}`);
  token = (await response.json()).access_token;
}
for (let run = 1; run <= Number(count); run++) {
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
  });
  try {
    const page = await browser.newPage();
    const requestor = target === 'summary' ? async () => {
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      await page.evaluate(value => {
        document.querySelector('#token').value = value;
        document.querySelector('#connectionForm').requestSubmit();
      }, token);
      await page.waitForSelector('.metrics-grid', { timeout: 15000 });
    } : url;
    const result = await navigation(page, requestor, { config, flags: {
      onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
      disableStorageReset: false,
    } });
    const lhr = result.lhr;
    if (lhr.runtimeError) throw new Error(lhr.runtimeError.message);
    const prefix = resolve(outputDir, `${target}-${mode}-${run}`);
    await writeFile(`${prefix}.report.json`, redact(JSON.stringify(lhr, null, 2)));
    const html = ReportGenerator.generateReport(lhr, 'html').replace(/^[\t ]+$/gm, '');
    await writeFile(`${prefix}.report.html`, redact(html));
    if (run === 1) {
      // Preserve the trace for diagnosis separately from the score report.
      if (result.artifacts?.Trace) await writeFile(`${prefix}.trace.json`, redact(JSON.stringify(result.artifacts.Trace)));
      await page.screenshot({ path: `${prefix}.page.png`, fullPage: true });
      const reportPage = await browser.newPage();
      await reportPage.setViewport({ width: 1440, height: 1100 });
      await reportPage.goto(pathToFileURL(`${prefix}.report.html`).href, { waitUntil: 'load' });
      await reportPage.waitForSelector('.lh-category');
      await reportPage.screenshot({ path: `${prefix}.report.png` });
    }
    console.log(JSON.stringify({ target, mode, run, scores: Object.fromEntries(
      Object.entries(lhr.categories).map(([key, value]) => [key, Math.round(value.score * 100)])),
      metrics: Object.fromEntries(['server-response-time', 'largest-contentful-paint',
        'cumulative-layout-shift', 'total-blocking-time'].map(key => [key, lhr.audits[key].numericValue])),
    }));
  } finally {
    await browser.close();
  }
}
