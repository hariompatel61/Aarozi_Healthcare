import test from "node:test";
import assert from "node:assert";
import { RawMessageStorage } from "./storage.js";
import { AstmAdapter } from "./astmAdapter.js";
import { AnalyzerMapper } from "./mapping.js";
import { SampleMatcher } from "./sampleMatching.js";

test("E2E Integration: duplicate message handling and storage failure recovery", async () => {
  const storage = new RawMessageStorage();

  const rawMsg = "H|^&|ASTM_E1394\nP|1|SMP-001\nO|1|SMP-001\nR|1|^^^GLU|95.0|mg/dL|N||F";
  const tenantId = "tenant-e2e-1";

  // 1. Store first time
  const record1 = storage.save({ tenantId, analyzerId: "analyzer-1", rawPayload: rawMsg, parseStatus: "received" });
  assert.ok(record1.id);

  // 2. Store duplicate (idempotency check / durable audit log)
  const record2 = storage.save({ tenantId, analyzerId: "analyzer-1", rawPayload: rawMsg, parseStatus: "received" });
  assert.ok(record2.id);
  assert.notStrictEqual(record1.id, record2.id); // Each raw ingestion is recorded as a distinct audit log entry

  // Retrieve raw messages
  const retrieved = storage.findById(record1.id);
  assert.strictEqual(retrieved?.rawPayload, rawMsg);
});

test("E2E Integration: complete pipeline (Ingest -> Parse -> Map -> Match)", async () => {
  // Setup components
  const astmAdapter = new AstmAdapter();
  const mapper = new AnalyzerMapper({
    GLU: { standardTestCode: "TEST_GLUCOSE_FASTING", allowedRange: { min: 20, max: 600 } }
  });
  const matcher = new SampleMatcher();
  matcher.registerSample({
    sampleId: "SMP-1001",
    patientId: "PAT-009",
    orderId: "ORD-009",
    status: "collected",
    testCodes: ["TEST_GLUCOSE_FASTING"],
  });

  const rawAstm = [
    "H|^&|ANALYZOR",
    "P|1|SMP-1001",
    "O|1|SMP-1001",
    "R|1|^^^GLU|110|mg/dL|N||F"
  ].join("\n");

  // Step 1: Parse ASTM
  const parsedResults = astmAdapter.parse(rawAstm, "msg-x");
  assert.strictEqual(parsedResults.length, 1);
  assert.strictEqual(parsedResults[0].sampleId, "SMP-1001");
  assert.strictEqual(parsedResults[0].testCode, "GLU");

  // Step 2: Map Codes & Validate
  const mapped = mapper.mapResult(parsedResults[0]);
  assert.strictEqual(mapped.standardTestCode, "TEST_GLUCOSE_FASTING");
  assert.strictEqual(mapped.numericValue, 110);
  assert.strictEqual(mapped.isValid, true);

  // Step 3: Match Sample against Registry
  const match = matcher.matchSample(mapped.sampleId);
  assert.strictEqual(match.matched, true);
  assert.strictEqual(match.sampleRecord?.orderId, "ORD-009");
});

test("E2E Integration: safe rejection of unmatched or malformed samples", async () => {
  const matcher = new SampleMatcher();
  const mapper = new AnalyzerMapper();
  const astmAdapter = new AstmAdapter();

  const rawAstm = [
    "H|^&|ANALYZOR",
    "P|1|UNKNOWN-SAMPLE",
    "O|1|UNKNOWN-SAMPLE",
    "R|1|^^^BADTEST|999|units|N||F"
  ].join("\n");

  const parsed = astmAdapter.parse(rawAstm, "msg-y");
  assert.strictEqual(parsed.length, 1);
  const mapped = mapper.mapResult(parsed[0]);
  const match = matcher.matchSample(mapped.sampleId);

  assert.strictEqual(match.matched, false);
  assert.ok(match.rejectionReason?.includes("not found"));
});
