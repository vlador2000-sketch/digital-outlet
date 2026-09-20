const catalogTimeZone = 'Europe/Podgorica';
const livePanelPasswordHash = '432a3b6e71e25d3ceab300e217f7fd3a20fb132df9e5ab66853d153863440a28';
const newVisitorsPerIpPerHour = 60;
const catalogDayFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: catalogTimeZone, year: 'numeric', month: '2-digit', day: '2-digit'
});

function catalogDay(timestamp) {
  const parts = catalogDayFormatter.formatToParts(new Date(timestamp));
  const value = type => parts.find(part => part.type === type).value;
  return `${value('year')}-${value('month')}-${value('day')}`;
}

async function sha256Hex(value) {
  const bytes = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)));
  return [...bytes].map(byte => byte.toString(16).padStart(2, '0')).join('');
}

function equalHash(a, b) {
  if (a.length !== b.length) return false;
  let difference = 0;
  for (let index = 0; index < a.length; index++) difference |= a.charCodeAt(index) ^ b.charCodeAt(index);
  return difference === 0;
}

async function isLivePanelAuthorized(request) {
  const authorization = request.headers.get('Authorization') || '';
  if (!authorization.startsWith('Basic ')) return false;
  try {
    const decoded = atob(authorization.slice(6));
    const separator = decoded.indexOf(':');
    if (separator < 0) return false;
    return equalHash(await sha256Hex(decoded.slice(separator + 1)), livePanelPasswordHash);
  } catch {
    return false;
  }
}

function livePanelChallenge() {
  return new Response('Authentication required', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="DiGiTaL LIVE", charset="UTF-8"',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Robots-Tag': 'noindex, nofollow'
    }
  });
}

export class CatalogPresence {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
    this.ctx.blockConcurrencyWhile(async () => {
      this.ctx.storage.sql.exec(`
        CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY,
          first_seen INTEGER NOT NULL,
          last_seen INTEGER NOT NULL,
          day TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS counters (
          key TEXT PRIMARY KEY,
          value INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS visitor_rate_limits (
          ip TEXT PRIMARY KEY,
          hour_bucket INTEGER NOT NULL,
          new_visitor_count INTEGER NOT NULL
        );
      `);
    });
  }

  async fetch(request) {
    const url = new URL(request.url);
    const now = Date.now();
    // Select a fresh daily bucket at local midnight; never erase stored counters.
    const day = catalogDay(now);

    if (url.pathname === '/ping' && request.method === 'POST') {
      let id = '';
      try {
        const body = await request.json();
        id = String(body.id || '').slice(0,100);
      } catch {}
      if (!id) return new Response('bad request', {status:400});

      const existing = [...this.ctx.storage.sql.exec('SELECT id FROM sessions WHERE id = ? LIMIT 1', id)];
      if (existing.length === 0) {
        const ip = String(request.headers.get('X-Catalog-Client-IP') || 'unknown').slice(0, 64);
        const hourBucket = Math.floor(now / (60 * 60 * 1000));
        const limitRows = [...this.ctx.storage.sql.exec('SELECT hour_bucket, new_visitor_count FROM visitor_rate_limits WHERE ip = ? LIMIT 1', ip)];
        const previous = limitRows[0];
        const count = previous?.hour_bucket === hourBucket ? Number(previous.new_visitor_count) : 0;
        if (count >= newVisitorsPerIpPerHour) return new Response(null, {status:204});
        this.ctx.storage.sql.exec(
          'INSERT INTO visitor_rate_limits (ip, hour_bucket, new_visitor_count) VALUES (?, ?, 1) ON CONFLICT(ip) DO UPDATE SET hour_bucket = excluded.hour_bucket, new_visitor_count = CASE WHEN visitor_rate_limits.hour_bucket = excluded.hour_bucket THEN visitor_rate_limits.new_visitor_count + 1 ELSE 1 END',
          ip, hourBucket
        );
        this.ctx.storage.sql.exec('INSERT INTO sessions (id, first_seen, last_seen, day) VALUES (?, ?, ?, ?)', id, now, now, day);
        this.ctx.storage.sql.exec("INSERT INTO counters (key,value) VALUES ('total',1) ON CONFLICT(key) DO UPDATE SET value=value+1");
        this.ctx.storage.sql.exec('INSERT INTO counters (key,value) VALUES (?,1) ON CONFLICT(key) DO UPDATE SET value=value+1', 'day:'+day);
      } else {
        this.ctx.storage.sql.exec('UPDATE sessions SET last_seen = ? WHERE id = ?', now, id);
      }
      // Keep only recent session rows; aggregate counters remain permanent.
      this.ctx.storage.sql.exec('DELETE FROM sessions WHERE last_seen < ?', now - 2*24*60*60*1000);
      return new Response(null, {status:204});
    }

    if (url.pathname === '/stats' && request.method === 'GET') {
      const activeAfter = now - 90000;
      const onlineRows = [...this.ctx.storage.sql.exec('SELECT COUNT(*) AS n FROM sessions WHERE last_seen >= ?', activeAfter)];
      const totalRows = [...this.ctx.storage.sql.exec("SELECT value FROM counters WHERE key='total'")];
      const todayRows = [...this.ctx.storage.sql.exec('SELECT value FROM counters WHERE key = ?', 'day:'+day)];
      const data = {
        online: Number(onlineRows[0]?.n || 0),
        today: Number(todayRows[0]?.value || 0),
        total: Number(totalRows[0]?.value || 0),
        day,
        time_zone: catalogTimeZone,
        window_seconds: 90,
        updated_at: new Date(now).toISOString()
      };
      return Response.json(data, {headers:{'cache-control':'no-store'}});
    }
    return new Response('not found', {status:404});
  }
}

const dashboard = `<!doctype html>
<html lang="sr-Latn-ME"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>DiGiTaL LIVE</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#050b13;color:#f4f8ff;font-family:system-ui,Arial}.box{width:min(92vw,620px);padding:28px;border:1px solid #244566;border-radius:24px;background:#0b1727;box-shadow:0 20px 60px #0009}h1{margin:0 0 8px;font-size:32px}.muted{color:#9db1c8}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:24px}.card{padding:20px 12px;border-radius:18px;background:#10233b;text-align:center}.n{font-size:40px;font-weight:900}.l{font-size:13px;color:#a9bdd4;margin-top:4px}@media(max-width:560px){.grid{grid-template-columns:1fr}.n{font-size:34px}}</style></head>
<body><main class="box"><h1>DiGiTaL LIVE</h1><div class="muted">Privatni pregled kataloga · osvježavanje na 10 s</div><div class="grid"><div class="card"><div class="n" id="o">—</div><div class="l">🟢 ONLINE SADA</div></div><div class="card"><div class="n" id="d">—</div><div class="l">👥 DANAS</div></div><div class="card"><div class="n" id="t">—</div><div class="l">📊 UKUPNO POSJETA</div></div></div><p class="muted" id="u"></p></main>
<script>async function load(){try{const r=await fetch('/__stats',{cache:'no-store'});const x=await r.json();o.textContent=x.online;d.textContent=x.today;t.textContent=x.total;u.textContent='Ažurirano: '+new Date(x.updated_at).toLocaleTimeString('sr-ME');}catch(e){u.textContent='Privremeno nema podataka';}}load();setInterval(load,10000);</script></body></html>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();

    if (path === '/__presence' && request.method === 'POST') {
      const id = env.CATALOG_PRESENCE.idFromName('digital-catalog');
      const stub = env.CATALOG_PRESENCE.get(id);
      const headers = new Headers(request.headers);
      headers.set('X-Catalog-Client-IP', request.headers.get('CF-Connecting-IP') || 'unknown');
      return stub.fetch('https://presence.internal/ping', new Request(request, {headers}));
    }

    if (path === '/__stats' && request.method === 'GET') {
      if (!await isLivePanelAuthorized(request)) return livePanelChallenge();
      const id = env.CATALOG_PRESENCE.idFromName('digital-catalog');
      const stub = env.CATALOG_PRESENCE.get(id);
      return stub.fetch('https://presence.internal/stats');
    }

    if (path === '/digital-live-7k9m2p4x') {
      if (!await isLivePanelAuthorized(request)) return livePanelChallenge();
      return new Response(dashboard, {headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-store','x-robots-tag':'noindex, nofollow'}});
    }

    if (path === '/digital') {
      url.pathname = '/DiGiTaL.html';
      return env.ASSETS.fetch(new Request(url, request));
    }

    return env.ASSETS.fetch(request);
  }
};
