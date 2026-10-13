import test from "node:test";
import assert from "node:assert";
import { SampleMatcher, SampleRecord } from "./sampleMatching.js";

test("SampleMatcher successfully matches registered samples", () => {
  const matcher = new SampleMatcher();
  const sample: SampleRecord = {
    sampleId: "SMP-100",
    patientId: "PAT-001",
    orderId: "ORD-001",
    status: "collected",
    testCodes: ["GLU", "CHOL"],
  };

  matcher.registerSample(sample);

  const match = matcher.matchSample("SMP-100");
  assert.strictEqual(match.matched, true);
  assert.strictEqual(match.sampleRecord?.patientId, "PAT-001");
  assert.strictEqual(match.rejectionReason, undefined);
});

test("SampleMatcher performs safe rejection for unknown or invalid samples", () => {
  const matcher = new SampleMatcher();

  const unknownMatch = matcher.matchSample("UNKNOWN-999");
  assert.strictEqual(unknownMatch.matched, false);
  assert.ok(unknownMatch.rejectionReason?.includes("not found"));

  const emptyMatch = matcher.matchSample("");
  assert.strictEqual(emptyMatch.matched, false);
  assert.ok(emptyMatch.rejectionReason?.includes("Missing or invalid"));
});
