/**
 * Serves the SPA under the /ep-farm-sim base path (tools.justinwong.io/ep-farm-sim).
 *
 * The asset router matches first, so requests that hit this worker are the ones
 * carrying the base prefix (or SPA deep links): strip the prefix and re-resolve
 * against the asset directory. Because every built URL starts with /ep-farm-sim/
 * (vite base), the old windrow.justinjywong.workers.dev root URL keeps working —
 * its asset requests carry the prefix too and land here.
 */
const BASE = "/ep-farm-sim";

export default {
  async fetch(request: Request, env: { ASSETS: { fetch: (r: Request) => Promise<Response> } }): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === BASE) {
      // ensure a trailing slash so the page's relative ./data/ fetches resolve under the base
      url.pathname = BASE + "/";
      return Response.redirect(url.toString(), 301);
    }
    if (url.pathname.startsWith(BASE + "/")) {
      url.pathname = url.pathname.slice(BASE.length);
    }
    return env.ASSETS.fetch(new Request(url.toString(), request));
  },
};
