import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = fs.readFileSync(path.join(root, 'DiGiTaL.html'), 'utf8');
const tags = html.match(/<img\b[^>]*>/gi) ?? [];
const covers = tags.filter(tag => /\bclass\s*=\s*["'][^"']*\bcover\b[^"']*["']/i.test(tag));
let localCount = 0;
let externalCount = 0;
const errors = [];

for (const tag of covers) {
  const src = tag.match(/\bsrc\s*=\s*["']([^"']+)["']/i)?.[1];
  const name = tag.match(/\balt\s*=\s*["']([^"']+)["']/i)?.[1] || 'Nepoznata igra';
  if (!src) {
    errors.push(`${name}: nedostaje src atribut`);
    continue;
  }
  if (!src.startsWith('/covers/')) {
    externalCount++;
    if (!/^https:\/\//.test(src)) errors.push(`${name}: neuobičajen izvor slike ${src}`);
    continue;
  }
  localCount++;
  let relativePath;
  try {
    relativePath = decodeURIComponent(src.split(/[?#]/)[0]).replace(/^\/+/, '');
  } catch {
    errors.push(`${name}: neispravan URL slike ${src}`);
    continue;
  }
  if (!/^covers\/[a-zA-Z0-9._/-]+$/.test(relativePath) || relativePath.includes('..')) {
    errors.push(`${name}: nedozvoljena putanja ${relativePath}`);
    continue;
  }
  const file = path.join(root, relativePath);
  if (!fs.existsSync(file)) {
    errors.push(`${name}: ne postoji ${relativePath}`);
    continue;
  }
  const bytes = fs.readFileSync(file);
  const jpeg = bytes.length >= 3 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
  const png = bytes.length >= 8 && bytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10]));
  const webp = bytes.length >= 12 && bytes.toString('ascii', 0, 4) === 'RIFF' && bytes.toString('ascii', 8, 12) === 'WEBP';
  if (!jpeg && !png && !webp) errors.push(`${name}: fajl nije validan JPEG/PNG/WEBP: ${relativePath}`);
}

console.log(`Provjereno ${covers.length} omota: ${localCount} lokalnih, ${externalCount} spoljnih.`);
console.log('Spoljni izvori nijesu pouzdani kao lokalni i ne mogu se ovom provjerom garantovati.');
if (errors.length) {
  console.error('Greške omota:\n' + errors.map(x => '- ' + x).join('\n'));
  process.exitCode = 1;
} else {
  console.log('Svi lokalni omoti postoje i imaju prepoznatljiv format slike.');
}
