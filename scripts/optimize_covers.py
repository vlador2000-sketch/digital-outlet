from __future__ import annotations
import base64, html as htmllib, io, re, time, unicodedata
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps
from ddgs import DDGS

HTML = Path('DiGiTaL.html')
OUT = Path('covers')
OUT.mkdir(exist_ok=True)
raw = HTML.read_text(encoding='utf-8')

card_re = re.compile(r'<article class="card">.*?</article>', re.S)
cards = card_re.findall(raw)
if len(cards) != 86:
    raise SystemExit(f'ABORT: expected 86 cards, found {len(cards)}')


def text_between(block, cls):
    m = re.search(rf'<div class="{re.escape(cls)}">(.*?)</div>', block, re.S)
    return htmllib.unescape(re.sub('<[^>]+>', '', m.group(1)).strip()) if m else ''


def get_src(block):
    m = re.search(r'<img[^>]*class="cover"[^>]*src="([^"]+)"', block, re.S)
    if not m:
        m = re.search(r'<img[^>]*src="([^"]+)"[^>]*class="cover"', block, re.S)
    return htmllib.unescape(m.group(1)) if m else None


sig_before = [(text_between(c, 'game'), text_between(c, 'price')) for c in cards]

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
})


def safe_slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii').lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:72] or 'cover'


def decode_source(src):
    if src.startswith('data:image/'):
        try:
            _, payload = src.split(',', 1)
            return base64.b64decode(payload)
        except Exception:
            return None
    if src.startswith(('http://', 'https://')):
        try:
            r = session.get(src, timeout=18, allow_redirects=True)
            if r.ok and len(r.content) > 1000:
                return r.content
        except Exception:
            return None
    p = Path(src.lstrip('/')) if src.startswith('/') else Path(src)
    try:
        return p.read_bytes() if p.exists() else None
    except Exception:
        return None


def image_info(data):
    if not data:
        return None
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.load()
            return im.width, im.height, im.format
    except Exception:
        return None


def title_tokens(title):
    stop = {'ps4', 'ps5', 'the', 'and', 'of', 'edition', 'collection', 'bundle', 'game', 'for', 'a', 'an', 'remastered', 'standard'}
    t = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii').lower()
    return [x for x in re.findall(r'[a-z0-9]+', t) if len(x) > 1 and x not in stop]


def score_text(title, s):
    toks = title_tokens(title)
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').lower()
    if not toks:
        return 0
    return sum(1 for t in toks if t in s) / len(toks)


def candidate_bytes(url):
    try:
        r = session.get(url, timeout=16, allow_redirects=True, stream=True)
        if not r.ok:
            return None
        size = int(r.headers.get('content-length') or 0)
        if size and size > 12_000_000:
            return None
        data = r.raw.read(12_000_001)
        if len(data) > 12_000_000 or len(data) < 3000:
            return None
        return data
    except Exception:
        return None


def best_search_image(title):
    queries = [
        f'"{title}" PS5 PS4 cover',
        f'"{title}" PlayStation cover art',
        f'"{title}" game cover',
    ]
    results = []
    try:
        ddgs = DDGS()
        for q in queries:
            try:
                for r in ddgs.images(q, max_results=30):
                    u = r.get('image') or ''
                    if not u.startswith('http'):
                        continue
                    domain = urlparse(u).netloc.lower()
                    meta = ' '.join([r.get('title') or '', r.get('url') or '', u])
                    match = score_text(title, meta)
                    if match < 0.55:
                        continue
                    bonus = 0
                    if 'image.api.playstation.com' in domain:
                        bonus += 100
                    elif 'playstation' in domain:
                        bonus += 70
                    elif any(x in domain for x in [
                        'ea.com', 'konami.com', 'ubisoft.com', 'rockstargames.com',
                        'bandainamcoent.com', 'capcom.com', '2k.com', 'bethesda.net',
                        'square-enix.com', 'sega.com', 'warnerbrosgames.com', 'epicgames.com',
                    ]):
                        bonus += 35
                    results.append((bonus + match * 50, u, meta))
            except Exception as e:
                print('SEARCH WARN', title, type(e).__name__, str(e)[:120])
    except Exception as e:
        print('SEARCH INIT WARN', title, type(e).__name__, str(e)[:120])

    seen = set()
    best = None
    for base_score, u, meta in sorted(results, reverse=True):
        if u in seen:
            continue
        seen.add(u)
        data = candidate_bytes(u)
        info = image_info(data)
        if not info:
            continue
        w, h, _ = info
        if w < 650 or h < 650:
            continue
        ratio = w / h
        if 0.58 <= ratio <= 0.85:
            aspect_bonus = 30
        elif 0.85 < ratio <= 1.08:
            aspect_bonus = 8
        else:
            continue
        final = base_score + aspect_bonus + min(w * h / 1_000_000, 8)
        if best is None or final > best[0]:
            best = (final, data, u, info)
        if final >= 150:
            break
    if best:
        _, data, u, info = best
        return data, u, info
    return None


rows = []
unresolved = []
new_cards = []
used_names = set()
total_before_embedded = 0
total_after = 0

for i, block in enumerate(cards, 1):
    title = text_between(block, 'game') or f'Game {i}'
    price = text_between(block, 'price')
    src = get_src(block)
    if not src:
        unresolved.append((title, 'missing src'))
        new_cards.append(block)
        continue

    original = decode_source(src)
    info = image_info(original)
    if info:
        ow, oh, _ = info
    else:
        ow = oh = 0
    if src.startswith('data:image/') and original:
        total_before_embedded += len(original)

    low = (not info) or ow < 380 or oh < 480
    chosen = original
    chosen_url = src
    action = 'compressed original'

    if low:
        found = best_search_image(title)
        if found:
            chosen, chosen_url, ninfo = found
            action = 'replaced low-res source'
            print(f'REPLACED: {title}: {ow}x{oh} -> {ninfo[0]}x{ninfo[1]} | {chosen_url}')
        else:
            unresolved.append((title, f'no high-res replacement found; original {ow}x{oh}'))
            new_cards.append(block)
            continue

    if not chosen:
        found = best_search_image(title)
        if found:
            chosen, chosen_url, _ = found
            action = 'replaced unavailable source'
        else:
            unresolved.append((title, 'source unavailable and no replacement found'))
            new_cards.append(block)
            continue

    try:
        with Image.open(io.BytesIO(chosen)) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGB')
            if im.mode == 'RGBA':
                bg = Image.new('RGB', im.size, 'white')
                bg.paste(im, mask=im.getchannel('A'))
                im = bg
            if im.width > 420 or im.height > 680:
                im.thumbnail((420, 680), Image.Resampling.LANCZOS)
            quality = 70
            out = io.BytesIO()
            im.save(out, 'WEBP', quality=quality, method=6, optimize=True)
            while out.tell() > 58_000 and quality > 52:
                quality -= 3
                out = io.BytesIO()
                im.save(out, 'WEBP', quality=quality, method=6, optimize=True)
            if out.tell() > 70_000 and im.width > 360:
                scale = 360 / im.width
                im = im.resize((360, max(1, round(im.height * scale))), Image.Resampling.LANCZOS)
                quality = 60
                out = io.BytesIO()
                im.save(out, 'WEBP', quality=quality, method=6, optimize=True)
            data_out = out.getvalue()
            nw, nh = im.size
    except Exception as e:
        unresolved.append((title, f'encode failed: {e}'))
        new_cards.append(block)
        continue

    slug = safe_slug(title)
    base = slug
    n = 2
    while slug in used_names:
        slug = f'{base}-{n}'
        n += 1
    used_names.add(slug)
    rel = f'covers/{slug}.webp'
    Path(rel).write_bytes(data_out)
    total_after += len(data_out)
    new_src = '/' + rel

    qsrc = src.replace('&', '&amp;')
    replaced = block.replace(f'src="{qsrc}"', f'src="{new_src}"', 1)
    if replaced == block:
        replaced = block.replace(f'src="{src}"', f'src="{new_src}"', 1)
    if replaced == block:
        unresolved.append((title, 'could not rewrite src safely'))
        new_cards.append(block)
        continue

    new_cards.append(replaced)
    rows.append({
        'game': title,
        'price': price,
        'before': f'{ow}x{oh}' if info else 'unavailable',
        'after': f'{nw}x{nh}',
        'bytes': len(data_out),
        'quality': quality,
        'action': action,
        'source': chosen_url,
        'file': rel,
    })
    time.sleep(0.04)

if unresolved:
    print('\nUNRESOLVED COVERS:')
    for title, why in unresolved:
        print(f' - {title}: {why}')
    print(f'\nResolved {len(rows)}/86; unresolved {len(unresolved)}')
    raise SystemExit(2)

it = iter(new_cards)
rewritten = card_re.sub(lambda m: next(it), raw)
out_cards = card_re.findall(rewritten)
sig_after = [(text_between(c, 'game'), text_between(c, 'price')) for c in out_cards]
if sig_after != sig_before:
    raise SystemExit('ABORT: game names/prices changed')
if len(out_cards) != 86:
    raise SystemExit('ABORT: card count changed')
if 'data:image/' in ''.join(out_cards):
    raise SystemExit('ABORT: embedded cover data remained')
HTML.write_text(rewritten, encoding='utf-8')

report = Path('cover-optimization-report.md')
before_html = len(raw.encode('utf-8'))
after_html = len(rewritten.encode('utf-8'))
with report.open('w', encoding='utf-8') as f:
    f.write('# Catalog cover optimization report\n\n')
    f.write(f'- Cards: 86\n- HTML before: {before_html:,} bytes\n- HTML after: {after_html:,} bytes\n')
    f.write(f'- Optimized local covers: {len(rows)}\n- Total optimized cover bytes: {total_after:,}\n')
    f.write(f'- Embedded image bytes removed from HTML (decoded): {total_before_embedded:,}\n\n')
    f.write('| Game | Before | After | WebP | Action |\n|---|---:|---:|---:|---|\n')
    for r in rows:
        f.write(f"| {r['game'].replace('|','/')} | {r['before']} | {r['after']} | {r['bytes']/1024:.1f} KB | {r['action']} |\n")

print(f'OK: all 86 covers optimized. HTML {before_html:,} -> {after_html:,} bytes; covers total {total_after:,} bytes.')
