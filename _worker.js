export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);

    const url = new URL(request.url);
    if (url.pathname !== "/DiGiTaL.html") return response;

    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("text/html")) return response;

    const html = await response.text();
    const cleaned = html.replace(
      /<article class="card">(?:(?!<\/article>)[\s\S])*?alt="Maneater"(?:(?!<\/article>)[\s\S])*?<\/article>/i,
      ""
    );

    return new Response(cleaned, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers
    });
  }
};
