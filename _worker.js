export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const url = new URL(request.url);

    if (!url.pathname.toLowerCase().endsWith("/digital.html")) return response;

    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("text/html")) return response;

    const html = await response.text();

    // Remove the complete sold MANEATER product card, regardless of
    // attribute order/capitalization, while leaving every other card intact.
    const cleaned = html.replace(
      /<article\b[^>]*class=["'][^"']*\bcard\b[^"']*["'][^>]*>(?:(?!<\/article>)[\s\S])*?maneater(?:(?!<\/article>)[\s\S])*?<\/article>/gi,
      ""
    );

    return new Response(cleaned, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers
    });
  }
};
