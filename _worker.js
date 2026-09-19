export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();

    if (path === "/__visit" && request.method === "POST") {
      let visitor = "";
      try {
        const body = await request.json();
        visitor = String(body.id || "").slice(0, 100);
      } catch {}
      console.log(JSON.stringify({
        type: "catalog_visit",
        visitor,
        path: "/DiGiTaL",
        country: request.cf?.country || null,
        city: request.cf?.city || null,
        device: request.headers.get("user-agent") || null,
        referer: request.headers.get("referer") || null,
        ts: new Date().toISOString()
      }));
      return new Response(null, { status: 204 });
    }

    if (path === "/digital") {
      url.pathname = "/DiGiTaL.html";
      return env.ASSETS.fetch(new Request(url, request));
    }

    return env.ASSETS.fetch(request);
  }
};

// Restore last known-good catalog deployment.
