export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();
    const acceptsHtml = (request.headers.get("accept") || "").includes("text/html");

    if (acceptsHtml && !path.startsWith("/_")) {
      console.log({
        type: "page_view",
        path: path === "/digital" ? "/digital" : url.pathname,
        country: request.cf?.country || "unknown",
        timestamp: new Date().toISOString()
      });
    }

    if (path === "/digital") {
      url.pathname = "/DiGiTaL.html";
      return env.ASSETS.fetch(new Request(url, request));
    }

    return env.ASSETS.fetch(request);
  }
};
