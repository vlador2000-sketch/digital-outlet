export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();

    // The catalog HTML is already clean in DiGiTaL.html.
    // Rewrite the friendly /DiGiTaL URL directly to that static asset
    // instead of downloading and parsing the whole HTML on every request.
    if (path === "/digital" || path === "/digital.html") {
      url.pathname = "/DiGiTaL.html";

      const assetRequest = new Request(url.toString(), request);
      const response = await env.ASSETS.fetch(assetRequest);

      const headers = new Headers(response.headers);
      headers.set(
        "cache-control",
        "public, max-age=60, stale-while-revalidate=300"
      );

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers
      });
    }

    return env.ASSETS.fetch(request);
  }
};
