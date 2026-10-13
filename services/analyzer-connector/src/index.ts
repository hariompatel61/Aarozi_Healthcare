import * as http from "http";
import { ProtocolAdapter, BaseAdapter } from "./adapter.js";
import { RawMessageStorage, defaultStorage } from "./storage.js";
import { AstmAdapter } from "./astmAdapter.js";
import { Hl7Adapter } from "./hl7Adapter.js";

export interface ConnectorConfig {
  port: number;
  tenantId?: string;
  stationId?: string;
  storage?: RawMessageStorage;
}

export function createConnectorServer(config: ConnectorConfig = { port: 4000 }, adapters: Map<string, ProtocolAdapter> = new Map()) {
  const storage = config.storage || defaultStorage;
  if (!adapters.has("ASTM")) {
    adapters.set("ASTM", new AstmAdapter());
  }
  if (!adapters.has("HL7")) {
    adapters.set("HL7", new Hl7Adapter());
  }

  const server = http.createServer((req: http.IncomingMessage, res: http.ServerResponse) => {
    const url = req.url || "";
    const method = req.method || "GET";

    if (method === "GET" && url === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          status: "ok",
          service: "analyzer-connector",
          timestamp: new Date().toISOString(),
          tenantId: config.tenantId || "default",
          stationId: config.stationId || "station-1",
          registeredAdapters: Array.from(adapters.keys()),
        })
      );
      return;
    }

    if (method === "POST" && url === "/message") {
      let body = "";
      req.on("data", (chunk: Buffer) => {
        body += chunk.toString();
      });
      req.on("end", () => {
        try {
          const tenantId = req.headers["x-tenant-id"] as string || config.tenantId || "default";
          const analyzerId = req.headers["x-analyzer-id"] as string || "default-analyzer";
          const protocol = req.headers["x-protocol"] as string || (body.includes("MSH|") ? "HL7" : "ASTM");

          const stored = storage.save({
            tenantId,
            analyzerId,
            rawPayload: body,
            parseStatus: "received",
          });

          const adapter = adapters.get(protocol) || new BaseAdapter(protocol);
          let parsedResults: any[] = [];
          try {
            if (!adapter.validate(body)) {
              storage.updateStatus(stored.id, "error", "Validation failed");
            } else {
              parsedResults = adapter.parse(body, stored.id);
              storage.updateStatus(stored.id, "parsed");
            }
          } catch (err: any) {
            storage.updateStatus(stored.id, "error", err.message || "Parse error");
          }

          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(
            JSON.stringify({
              status: "received",
              messageId: stored.id,
              bytes: body.length,
              parsedResults,
              parsedCount: parsedResults.length,
              timestamp: new Date().toISOString(),
            })
          );
        } catch (e: any) {
          res.writeHead(400, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: e.message || "Bad Request" }));
        }
      });
      return;
    }

    if (method === "GET" && url.startsWith("/messages")) {
      const tenantId = req.headers["x-tenant-id"] as string || config.tenantId || "default";
      const messages = storage.findByTenant(tenantId);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ messages }));
      return;
    }

    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Not Found" }));
  });

  return server;
}

if (require.main === module) {
  const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 4000;
  const server = createConnectorServer({ port });
  server.listen(port, () => {
    console.log(`Aarozi Analyzer Connector running on port ${port}`);
  });
}




