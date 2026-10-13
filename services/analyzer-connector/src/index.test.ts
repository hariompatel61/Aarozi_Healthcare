import test from "node:test";
import assert from "node:assert";
import http from "http";
import { createConnectorServer } from "./index.js";

test("analyzer connector health endpoint", async () => {
  const server = createConnectorServer({ port: 0 });
  await new Promise<void>((resolve) => server.listen(0, resolve));
  const address = server.address();
  const port = typeof address === "object" && address !== null ? address.port : 0;

  try {
    const res = await fetch(`http://localhost:${port}/health`);
    assert.strictEqual(res.status, 200);
    const data: any = await res.json();
    assert.strictEqual(data.status, "ok");
    assert.strictEqual(data.service, "analyzer-connector");
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
});

test("analyzer connector message ingestion endpoint", async () => {
  const server = createConnectorServer({ port: 0 });
  await new Promise<void>((resolve) => server.listen(0, resolve));
  const address = server.address();
  const port = typeof address === "object" && address !== null ? address.port : 0;

  try {
    const res = await fetch(`http://localhost:${port}/message`, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: "H|\\^&|ASTM_MSG",
    });
    assert.strictEqual(res.status, 200);
    const data: any = await res.json();
    assert.strictEqual(data.status, "received");
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
});
