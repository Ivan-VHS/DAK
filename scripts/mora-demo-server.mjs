import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer } from "node:http";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const files = new Map([
  ["/mora/demo.html", { file: "mora/demo.html", type: "text/html; charset=utf-8" }],
  ["/mora/demo.css", { file: "mora/demo.css", type: "text/css; charset=utf-8" }],
  ["/mora/demo.js", { file: "mora/demo.js", type: "text/javascript; charset=utf-8" }]
]);

export function createMoraDemoServer(root = repositoryRoot) {
  const resolvedRoot = path.resolve(root);

  return createServer(async (request, response) => {
    const method = request.method || "GET";
    if (method !== "GET" && method !== "HEAD") {
      response.writeHead(405, { Allow: "GET, HEAD", "Content-Type": "text/plain; charset=utf-8" });
      response.end("Method not allowed\n");
      return;
    }

    let pathname;
    try {
      pathname = decodeURIComponent(new URL(request.url || "/", "http://127.0.0.1").pathname);
    } catch {
      response.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Bad request\n");
      return;
    }

    if (pathname === "/") {
      response.writeHead(302, { Location: "/mora/demo.html", "Cache-Control": "no-store" });
      response.end();
      return;
    }

    const entry = files.get(pathname);
    if (!entry) {
      response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Not found\n");
      return;
    }

    const filePath = path.resolve(resolvedRoot, entry.file);
    if (!filePath.startsWith(resolvedRoot + path.sep)) {
      response.writeHead(404);
      response.end();
      return;
    }

    try {
      const metadata = await stat(filePath);
      response.writeHead(200, {
        "Content-Type": entry.type,
        "Content-Length": metadata.size,
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
      });
      if (method === "HEAD") {
        response.end();
        return;
      }
      createReadStream(filePath).pipe(response);
    } catch {
      response.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Unable to read demo asset\n");
    }
  });
}

const invokedPath = process.argv[1] ? path.resolve(process.argv[1]) : "";
if (invokedPath && pathToFileURL(invokedPath).href === import.meta.url) {
  const port = Number.parseInt(process.env.DUCKOS_DEMO_PORT || "8766", 10);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    console.error("DUCKOS_DEMO_PORT must be an integer from 0 to 65535.");
    process.exitCode = 2;
  } else {
    const server = createMoraDemoServer();
    server.listen(port, "127.0.0.1", () => {
      const address = server.address();
      console.log("Mora desktop demo: http://127.0.0.1:" + address.port + "/");
      console.log("Local-only server. Press Ctrl+C to stop.");
    });
    const shutdown = () => server.close(() => process.exit(0));
    process.once("SIGINT", shutdown);
    process.once("SIGTERM", shutdown);
  }
}