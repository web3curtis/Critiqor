globalThis.__nitro_main__ = import.meta.url;
import { N as NodeResponse, s as serve } from "./_libs/srvx.mjs";
import { H as HTTPError, d as defineHandler, t as toEventHandler, a as defineLazyEventHandler, b as H3Core } from "./_libs/h3.mjs";
import { d as decodePath, w as withLeadingSlash, a as withoutTrailingSlash, j as joinURL } from "./_libs/ufo.mjs";
import { promises } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import "node:http";
import "node:stream";
import "node:stream/promises";
import "node:https";
import "node:http2";
import "./_libs/rou3.mjs";
function lazyService(loader) {
  let promise, mod;
  return {
    fetch(req) {
      if (mod) {
        return mod.fetch(req);
      }
      if (!promise) {
        promise = loader().then((_mod) => mod = _mod.default || _mod);
      }
      return promise.then((mod2) => mod2.fetch(req));
    }
  };
}
const services = {
  ["ssr"]: lazyService(() => import("./_ssr/index.mjs"))
};
globalThis.__nitro_vite_envs__ = services;
const errorHandler$1 = (error, event) => {
  const res = defaultHandler(error, event);
  return new NodeResponse(typeof res.body === "string" ? res.body : JSON.stringify(res.body, null, 2), res);
};
function defaultHandler(error, event) {
  const unhandled = error.unhandled ?? !HTTPError.isError(error);
  const { status = 500, statusText = "" } = unhandled ? {} : error;
  if (status === 404) {
    const url = event.url || new URL(event.req.url);
    const baseURL = "/";
    if (/^\/[^/]/.test(baseURL) && !url.pathname.startsWith(baseURL)) {
      return {
        status: 302,
        headers: new Headers({ location: `${baseURL}${url.pathname.slice(1)}${url.search}` })
      };
    }
  }
  const headers2 = new Headers(unhandled ? {} : error.headers);
  headers2.set("content-type", "application/json; charset=utf-8");
  const jsonBody = unhandled ? {
    status,
    unhandled: true
  } : typeof error.toJSON === "function" ? error.toJSON() : {
    status,
    statusText,
    message: error.message
  };
  return {
    status,
    statusText,
    headers: headers2,
    body: {
      error: true,
      ...jsonBody
    }
  };
}
const errorHandlers = [errorHandler$1];
async function errorHandler(error, event) {
  for (const handler of errorHandlers) {
    try {
      const response = await handler(error, event, { defaultHandler });
      if (response) {
        return response;
      }
    } catch (error2) {
      console.error(error2);
    }
  }
}
const headers = ((m) => function headersRouteRule(event) {
  for (const [key2, value] of Object.entries(m.options || {})) {
    event.res.headers.set(key2, value);
  }
});
const assets = {
  "/assets/card-3trT3p6x.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"b88-OwR5MNzOKggbit3cpok2YoaljrQ"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 2952,
    "path": "../public/assets/card-3trT3p6x.js"
  },
  "/assets/checkbox-C_OZ0CGD.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"2b2-N6sf84hVN3h4bTIcq5FYJb6y5v8"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 690,
    "path": "../public/assets/checkbox-C_OZ0CGD.js"
  },
  "/assets/evidence-CdSLynlt.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"135e-5R/8BEqJMCd85nd2FvmMweXmn08"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 4958,
    "path": "../public/assets/evidence-CdSLynlt.js"
  },
  "/assets/diagnoses-m_npymSi.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"94e7-vF5yQXkwwjnZefIE9Ec++p2OPRs"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 38119,
    "path": "../public/assets/diagnoses-m_npymSi.js"
  },
  "/assets/playbook-BpV12O2I.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"144f-85RJBDCvZ6C7tnD8xDpC6nLIQX0"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 5199,
    "path": "../public/assets/playbook-BpV12O2I.js"
  },
  "/assets/run-selector-D0ijji2g.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"38a-HjyZImk+Ig8FlWXAJFvxk7Dlfyw"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 906,
    "path": "../public/assets/run-selector-D0ijji2g.js"
  },
  "/assets/runs-BUPkdfhf.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"19da-3bt4FteanPlt4qF7YAR/YMIxJW0"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 6618,
    "path": "../public/assets/runs-BUPkdfhf.js"
  },
  "/assets/appearance-gwAL_ked.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"53a-lbGgHMLmngLGdgomiMrWfU0HBw0"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 1338,
    "path": "../public/assets/appearance-gwAL_ked.js"
  },
  "/assets/react-vendor-D7KJJ4pD.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"31ef8-pI8JeMnNSBfOEV8Pu5MCJGcBAV8"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 204536,
    "path": "../public/assets/react-vendor-D7KJJ4pD.js"
  },
  "/assets/ui-vendor-B33jwOqA.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"f66a-s6ka4P5HibFqyB0H9y07rjSzABQ"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 63082,
    "path": "../public/assets/ui-vendor-B33jwOqA.js"
  },
  "/assets/styles-CPOj_Ctq.css": {
    "type": "text/css; charset=utf-8",
    "etag": '"17aaa-WlKSDMCp58hnV7+IOSb8C5Sq3tA"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 96938,
    "path": "../public/assets/styles-CPOj_Ctq.css"
  },
  "/assets/index-C6SLmSYf.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"228e-7lOrptft0B0rC/nFJDLj1EdHY6U"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 8846,
    "path": "../public/assets/index-C6SLmSYf.js"
  },
  "/assets/index-O-EJdERA.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"469b7-RMRs6Vg4o14dZ7VysiYLv194UOE"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 289207,
    "path": "../public/assets/index-O-EJdERA.js"
  },
  "/assets/settings-DcB4R2iF.js": {
    "type": "text/javascript; charset=utf-8",
    "etag": '"a66-jdU0DUC4Bk1eEsoweHj1tUld6vo"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 2662,
    "path": "../public/assets/settings-DcB4R2iF.js"
  },
  "/assets/critiqor-logo-v-ZKSU2V.png": {
    "type": "image/png",
    "etag": '"af113-z31pw/7m150Murb+Un/bCcfK6tE"',
    "mtime": "2026-09-01T08:22:49.928Z",
    "size": 717075,
    "path": "../public/assets/critiqor-logo-v-ZKSU2V.png"
  }
};
function readAsset(id) {
  const serverDir = dirname(fileURLToPath(globalThis.__nitro_main__));
  return promises.readFile(resolve(serverDir, assets[id].path));
}
const publicAssetBases = {};
function isPublicAssetURL(id = "") {
  if (assets[id]) {
    return true;
  }
  for (const base in publicAssetBases) {
    if (id.startsWith(base)) {
      return true;
    }
  }
  return false;
}
function getAsset(id) {
  return assets[id];
}
const METHODS = /* @__PURE__ */ new Set(["HEAD", "GET"]);
const EncodingMap = {
  gzip: ".gz",
  br: ".br",
  zstd: ".zst"
};
const _Z0tfeS = defineHandler((event) => {
  if (event.req.method && !METHODS.has(event.req.method)) {
    return;
  }
  let id = decodePath(withLeadingSlash(withoutTrailingSlash(event.url.pathname)));
  let asset;
  const encodingHeader = event.req.headers.get("accept-encoding") || "";
  const encodings = [...encodingHeader.split(",").map((e) => EncodingMap[e.trim()]).filter(Boolean).sort(), ""];
  for (const encoding of encodings) {
    for (const _id of [id + encoding, joinURL(id, "index.html" + encoding)]) {
      const _asset = getAsset(_id);
      if (_asset) {
        asset = _asset;
        id = _id;
        break;
      }
    }
  }
  if (!asset) {
    if (isPublicAssetURL(id)) {
      event.res.headers.delete("Cache-Control");
      throw new HTTPError({ status: 404 });
    }
    return;
  }
  if (encodings.length > 1) {
    event.res.headers.append("Vary", "Accept-Encoding");
  }
  const ifNotMatch = event.req.headers.get("if-none-match") === asset.etag;
  if (ifNotMatch) {
    event.res.status = 304;
    event.res.statusText = "Not Modified";
    return "";
  }
  const ifModifiedSinceH = event.req.headers.get("if-modified-since");
  const mtimeDate = new Date(asset.mtime);
  if (ifModifiedSinceH && asset.mtime && new Date(ifModifiedSinceH) >= mtimeDate) {
    event.res.status = 304;
    event.res.statusText = "Not Modified";
    return "";
  }
  if (asset.type) {
    event.res.headers.set("Content-Type", asset.type);
  }
  if (asset.etag && !event.res.headers.has("ETag")) {
    event.res.headers.set("ETag", asset.etag);
  }
  if (asset.mtime && !event.res.headers.has("Last-Modified")) {
    event.res.headers.set("Last-Modified", mtimeDate.toUTCString());
  }
  if (asset.encoding && !event.res.headers.has("Content-Encoding")) {
    event.res.headers.set("Content-Encoding", asset.encoding);
  }
  if (asset.size > 0 && !event.res.headers.has("Content-Length")) {
    event.res.headers.set("Content-Length", asset.size.toString());
  }
  return readAsset(id);
});
const findRouteRules = /* @__PURE__ */ (() => {
  const $0 = [{ name: "headers", route: "/assets/**", handler: headers, options: { "cache-control": "public, max-age=31536000, immutable" } }];
  return (m, p) => {
    let r = [];
    if (p.charCodeAt(p.length - 1) === 47) p = p.slice(0, -1) || "/";
    let s = p.split("/"), l = s.length;
    if (l > 1) {
      if (s[1] === "assets") {
        r.unshift({ data: $0, params: { "_": s.slice(2).join("/") } });
      }
    }
    return r;
  };
})();
const _lazy_NbKlO7 = defineLazyEventHandler(() => import("./_chunks/ssr-renderer.mjs"));
const findRoute = /* @__PURE__ */ (() => {
  const data = { route: "/**", handler: _lazy_NbKlO7 };
  return ((_m, p) => {
    return { data, params: { "_": p.slice(1) } };
  });
})();
const globalMiddleware = [
  toEventHandler(_Z0tfeS)
].filter(Boolean);
const APP_ID = "default";
function useNitroApp() {
  let instance = useNitroApp._instance;
  if (instance) {
    return instance;
  }
  instance = useNitroApp._instance = createNitroApp();
  globalThis.__nitro__ = globalThis.__nitro__ || {};
  globalThis.__nitro__[APP_ID] = instance;
  return instance;
}
function createNitroApp() {
  const hooks = void 0;
  const captureError = (error, errorCtx) => {
    if (errorCtx?.event) {
      const errors = errorCtx.event.req.context?.nitro?.errors;
      if (errors) {
        errors.push({
          error,
          context: errorCtx
        });
      }
    }
  };
  const h3App = createH3App({ onError(error, event) {
    return errorHandler(error, event);
  } });
  let appHandler = (req) => {
    req.context ||= {};
    req.context.nitro = req.context.nitro || { errors: [] };
    return h3App.fetch(req);
  };
  const app = {
    fetch: appHandler,
    h3: h3App,
    hooks,
    captureError
  };
  return app;
}
function createH3App(config) {
  const h3App = new H3Core(config);
  h3App["~findRoute"] = (event) => findRoute(event.req.method, event.url.pathname);
  h3App["~middleware"].push(...globalMiddleware);
  {
    h3App["~getMiddleware"] = (event, route) => {
      const pathname = event.url.pathname;
      const method = event.req.method;
      const middleware = [];
      {
        const routeRules = getRouteRules(method, pathname);
        event.context.routeRules = routeRules?.routeRules;
        if (routeRules?.routeRuleMiddleware.length) {
          middleware.push(...routeRules.routeRuleMiddleware);
        }
      }
      middleware.push(...h3App["~middleware"]);
      if (route?.data?.middleware?.length) {
        middleware.push(...route.data.middleware);
      }
      return middleware;
    };
  }
  return h3App;
}
function getRouteRules(method, pathname) {
  const m = findRouteRules(method, pathname);
  if (!m?.length) {
    return { routeRuleMiddleware: [] };
  }
  const routeRules = {};
  for (const layer of m) {
    for (const rule of layer.data) {
      const currentRule = routeRules[rule.name];
      if (currentRule) {
        if (rule.options === false) {
          delete routeRules[rule.name];
          continue;
        }
        if (typeof currentRule.options === "object" && typeof rule.options === "object") {
          currentRule.options = {
            ...currentRule.options,
            ...rule.options
          };
        } else {
          currentRule.options = rule.options;
        }
        currentRule.route = rule.route;
        currentRule.params = {
          ...currentRule.params,
          ...layer.params
        };
      } else if (rule.options !== false) {
        routeRules[rule.name] = {
          ...rule,
          params: layer.params
        };
      }
    }
  }
  const middleware = [];
  const orderedRules = Object.values(routeRules).sort((a, b) => (a.handler?.order || 0) - (b.handler?.order || 0));
  for (const rule of orderedRules) {
    if (rule.options === false || !rule.handler) {
      continue;
    }
    middleware.push(rule.handler(rule));
  }
  return {
    routeRules,
    routeRuleMiddleware: middleware
  };
}
function _captureError(error, type) {
  console.error(`[${type}]`, error);
  useNitroApp().captureError?.(error, { tags: [type] });
}
function trapUnhandledErrors() {
  process.on("unhandledRejection", (error) => _captureError(error, "unhandledRejection"));
  process.on("uncaughtException", (error) => _captureError(error, "uncaughtException"));
}
const tracingSrvxPlugins = [];
const _parsedPort = Number.parseInt(process.env.NITRO_PORT ?? process.env.PORT ?? "");
const port = Number.isNaN(_parsedPort) ? 3e3 : _parsedPort;
const host = process.env.NITRO_HOST || process.env.HOST;
const cert = process.env.NITRO_SSL_CERT;
const key = process.env.NITRO_SSL_KEY;
const nitroApp = useNitroApp();
serve({
  port,
  hostname: host,
  tls: cert && key ? {
    cert,
    key
  } : void 0,
  fetch: nitroApp.fetch,
  plugins: [...tracingSrvxPlugins]
});
trapUnhandledErrors();
const nodeServer = {};
export {
  nodeServer as default
};
