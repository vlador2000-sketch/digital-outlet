import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

const baseUrl = 'https://outlet.vlador2000.workers.dev/DiGiTaL.html';
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
await fs.mkdir('test-artifacts', { recursive: true });

try {
  for (const [label, width, height, expectedColumns] of [
    ['telefon', 390, 844, 2],
    ['racunar', 1440, 900, 4]
  ]) {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', err => errors.push(err.message));
    if (label === 'telefon') {
      await page.route('**/covers/quality-001-a-plague-tale-innocence.webp', route => route.abort('failed'));
    }
    const response = await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 45_000 });
    assert.equal(response?.status(), 200, 'OUTLET returns HTTP 200');
    await page.waitForSelector('#grid .card', { timeout: 15_000 });
    const cardCount = await page.locator('#grid .card').count();
    assert.equal(cardCount, 89, 'Expected 89 game cards, no removed titles');

    const columns = await page.locator('#grid').evaluate(el =>
      getComputedStyle(el).gridTemplateColumns.trim().split(/\s+/).length);
    assert.equal(columns, expectedColumns, label + ' must show ' + expectedColumns + ' columns');

    if (label === 'telefon') {
      await page.waitForFunction(() =>
        document.querySelector('img.cover')?.dataset.coverFallbackApplied === '1',
        { timeout: 15_000 });
      const src = await page.locator('img.cover').first().getAttribute('src');
      assert.match(src ?? '', /^data:image\/svg\+xml/, 'Fallback image must replace failed cover');
      await page.locator('#q').fill('ELDEN RING');
      const visible = await page.locator('#grid .card:visible').count();
      assert.equal(visible, 1, 'Game search still works after update');
      await page.locator('#q').clear();
      assert.equal(await page.locator('#grid .card:visible').count(), 89);
    }
    await page.screenshot({ path: 'test-artifacts/' + label + '.png', fullPage: false });
    assert.deepEqual(errors, [], 'Browser must have no unhandled JS errors');
    console.log('OK ' + label + ': ' + width + 'x' + height + ', ' + columns +
      ' columns, ' + cardCount + ' cards' + (label === 'telefon' ? ', fallback + filter OK' : ''));
    await page.close();
  }
} finally {
  await browser.close();
}