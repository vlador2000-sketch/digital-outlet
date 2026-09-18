export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();

    if (path === "/__presence") {
      if (request.headers.get("Upgrade") !== "websocket") {
        return new Response("WebSocket required", { status: 426 });
      }
      const id = env.PRESENCE.idFromName("digital-outlet-live");
      return env.PRESENCE.get(id).fetch(request);
    }

    if (path === "/__traffic") {
      return new Response(TRAFFIC_DASHBOARD, {
        headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" }
      });
    }

    const acceptsHtml = (request.headers.get("accept") || "").includes("text/html");

    if (path === "/digital") {
      url.pathname = "/DiGiTaL.html";
      const response = await env.ASSETS.fetch(new Request(url, request));
      return acceptsHtml ? addPresenceScript(response, url.origin) : response;
    }

    if (acceptsHtml && path.endsWith(".html")) {
      const response = await env.ASSETS.fetch(request);
      return addPresenceScript(response, url.origin);
    }

    return env.ASSETS.fetch(request);
  }
};

function addPresenceScript(response, origin) {
  if (!(response.headers.get("content-type") || "").includes("text/html")) return response;
  const script = `
<script>
(function(){
  try {
    if (window.__digitalPresenceStarted) return;
    window.__digitalPresenceStarted = true;
    var proto = location.protocol === "https:" ? "wss:" : "ws:";
    var ws = new WebSocket(proto + "//" + location.host + "/__presence?visitor=1");
    ws.onclose = function(){ setTimeout(function(){ location.reload(); }, 15000); };
  } catch(e) {}
})();
</script>`;
  return new HTMLRewriter()
    .on("body", { element(e) { e.append(script, { html: true }); } })
    .transform(response);
}

export class Presence {
  constructor(state, env) {
    this.ctx = state;
    this.env = env;
    this.ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair("ping", "pong"));
  }

  async fetch(request) {
    const url = new URL(request.url);
    const dashboard = url.searchParams.get("dashboard") === "1";
    const [client, server] = Object.values(new WebSocketPair());
    this.ctx.acceptWebSocket(server, dashboard ? ["dashboard"] : ["visitor"]);
    server.serializeAttachment({ dashboard });
    if (!dashboard) this.broadcast();
    else server.send(JSON.stringify({ type: "count", count: this.visitorCount() }));
    return new Response(null, { status: 101, webSocket: client });
  }

  webSocketMessage(ws, message) {
    if (message === "ping") return;
    if (this.ctx.getTags(ws).includes("dashboard")) {
      ws.send(JSON.stringify({ type: "count", count: this.visitorCount() }));
    }
  }

  webSocketClose(ws) {
    if (!this.ctx.getTags(ws).includes("dashboard")) this.broadcast();
  }

  visitorCount() {
    return this.ctx.getWebSockets("visitor").length;
  }

  broadcast() {
    const payload = JSON.stringify({ type: "count", count: this.visitorCount() });
    for (const ws of this.ctx.getWebSockets("dashboard")) {
      try { ws.send(payload); } catch {}
    }
  }
}

const TRAFFIC_DASHBOARD = `<!doctype html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DiGiTaL — Live Traffic</title>
<style>
body{margin:0;background:#0b0b0b;color:#fff;font-family:system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}
main{text-align:center;padding:40px}.n{font-size:96px;font-weight:800;line-height:1}.label{font-size:22px;margin-top:16px;color:#aaa}.dot{display:inline-block;width:12px;height:12px;border-radius:50%;background:#35d07f;margin-right:8px}
small{display:block;color:#666;margin-top:28px}
</style>
</head>
<body><main>
<div><span class="dot"></span><span>LIVE</span></div>
<div id="n" class="n">0</div>
<div class="label">aktivnih posjetilaca / sesija</div>
<small>DiGiTaL Outlet · automatsko ažuriranje</small>
</main>
<script>
(function(){
 var n=document.getElementById("n");
 var ws=new WebSocket((location.protocol==="https:"?"wss:":"ws:")+"//"+location.host+"/__presence?dashboard=1");
 ws.onmessage=function(e){try{var d=JSON.parse(e.data);if(d.type==="count")n.textContent=d.count}catch(_){}};
 ws.onclose=function(){setTimeout(function(){location.reload()},3000)};
})();
</script>
</body></html>`;

