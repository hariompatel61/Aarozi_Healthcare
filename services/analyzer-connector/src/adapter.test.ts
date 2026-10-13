import test from "node:test";
import assert from "node:assert";
import { BaseAdapter } from "./adapter.js";
import { RawMessageStorage } from "./storage.js";
import { createConnectorServer } from "./index.js";

test("BaseAdapter validation and parsing", () => {
  const adapter = new BaseAdapter("TEST");
  assert.strictEqual(adapter.getProtocolName(), "TEST");
  assert.strictEqual(adapter.validate("valid payload"), true);
  assert.strictEqual(adapter.validate("   "), false);
  
  const results = adapter.parse("some payload", "msg-1");
  assert.deepStrictEqual(results, []);
});

test("RawMessageStorage persistence and retrieval", () => {
  const storage = new RawMessageStorage();
  const saved = storage.save({
    tenantId: "tenant-a",
    analyzerId: "analyzer-1",
    rawPayload: "TEST_PAYLOAD",
    parseStatus: "received",
  });

  assert.ok(saved.id);
  assert.strictEqual(saved.tenantId, "tenant-a");
  assert.strictEqual(saved.parseStatus, "received");

  const tenantMessages = storage.findByTenant("tenant-a");
  assert.strictEqual(tenantMessages.length, 1);

  storage.updateStatus(saved.id, "parsed");
  const updated = storage.findById(saved.id);
  assert.strictEqual(updated?.parseStatus, "parsed");
});

test("Connector server stores raw message and returns messageId", async () => {
  const storage = new RawMessageStorage();
  const server = createConnectorServer({ port: 0, storage, tenantId: "tenant-x" });
  await new Promise<void>((resolve) => server.listen(0, resolve));
  const address = server.address();
  const port = typeof address === "object" && address !== null ? address.port : 0;

  try {
    const res = await fetch(`http://localhost:${port}/message`, {
      method: "POST",
      headers: {
        "Content-Type": "text/plain",
        "x-tenant-id": "tenant-x",
        "x-analyzer-id": "analyzer-99",
        "x-protocol": "CUSTOM",
      },
      body: "SAMPLE_RESULT_DATA",
    });

    assert.strictEqual(res.status, 200);
    const data: any = await res.json();
    assert.strictEqual(data.status, "received");
    assert.ok(data.messageId);

    const messages = storage.findByTenant("tenant-x");
    assert.strictEqual(messages.length, 1);
    assert.strictEqual(messages[0].rawPayload, "SAMPLE_RESULT_DATA");
    assert.strictEqual(messages[0].analyzerId, "analyzer-99");
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
});
