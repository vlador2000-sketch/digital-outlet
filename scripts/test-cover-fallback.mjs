import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { runInNewContext } from 'node:vm';
import { fileURLToPath } from 'node:url';

const script = fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), 'cover-fallback.js'), 'utf8');

function createImage(complete, naturalWidth) {
  const listeners = {};
  return {
    complete, naturalWidth, dataset: {}, src: '/covers/missing.jpg',
    srcset: 'test.webp 2x',
    removed: [],
    classList: { add() {} },
    addEventListener(event, fn) { listeners[event] = fn; },
    removeAttribute(name) { this.removed.push(name); if (name === 'srcset') delete this.srcset; },
    emitError() { listeners.error(); }
  };
}

function apply(images) {
  runInNewContext(script, {
    document: { querySelectorAll(selector) { assert.equal(selector, 'img.cover'); return images; } },
    encodeURIComponent
  });
}

test('ne dira ispravno ucitanu sliku', () => {
  const img = createImage(true, 320);
  apply([img]);
  assert.equal(img.src, '/covers/missing.jpg');
});

test('zamjenjuje sliku koja ranije nije ucitana', () => {
  const img = createImage(false, 0);
  apply([img]);
  img.emitError();
  assert.match(img.src, /^data:image\/svg\+xml/);
  assert.equal(img.dataset.coverFallbackApplied, '1');
  assert.deepEqual(img.removed, ['srcset']);
});

test('pokriva sliku koja je otkazala prije registracije handlera', () => {
  const img = createImage(true, 0);
  apply([img]);
  assert.match(img.src, /^data:image\/svg\+xml/);
});

test('ne ulazi u petlju ako zamjenska slika izazove error', () => {
  const img = createImage(false, 0);
  apply([img]);
  img.emitError();
  const fallback = img.src;
  img.emitError();
  assert.equal(img.src, fallback);
  assert.equal(img.removed.length, 1);
});
