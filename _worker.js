export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const url = new URL(request.url);

    const isCatalog =
      url.pathname.toLowerCase().endsWith("/digital.html") ||
      url.pathname.toLowerCase().endsWith("/digital");

    if (!isCatalog) return response;

    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("text/html")) return response;

    const html = await response.text();

    // Remove the complete sold MANEATER product card while leaving
    // every other catalog card unchanged.
    const cleaned = html.replace(
      /<article\b[^>]*class=["'][^"']*\bcard\b[^"']*["'][^>]*>(?:(?!<\/article>)[\s\S])*?maneater(?:(?!<\/article>)[\s\S])*?<\/article>/gi,
      ""
    );

    const headers = new Headers(response.headers);
    headers.set("cache-control", "no-store, no-cache, must-revalidate");

    return new Response(cleaned, {
      status: response.status,
      statusText: response.statusText,
      headers
    });
  }
};
