import test from "node:test";
import assert from "node:assert";
import { AnalyzerMapper, TestMappingConfig } from "./mapping.js";
import { ParsedResult } from "./adapter.js";

const sampleMapping: TestMappingConfig = {
  GLU: {
    standardTestCode: "TEST_GLUCOSE_FASTING",
    allowedRange: { min: 10, max: 1000 },
  },
  CHOL: {
    standardTestCode: "TEST_CHOLESTEROL_TOTAL",
    allowedRange: { min: 20, max: 800 },
  },
};

test("AnalyzerMapper maps codes and validates ranges", () => {
  const mapper = new AnalyzerMapper(sampleMapping);

  const parsedGlu: ParsedResult = {
    sampleId: "SMP-001",
    testCode: "GLU",
    value: "95.0",
    units: "mg/dL",
    flags: "N",
    timestamp: new Date().toISOString(),
    rawMessageId: "msg-1",
  };

  const mapped = mapper.mapResult(parsedGlu);
  assert.strictEqual(mapped.standardTestCode, "TEST_GLUCOSE_FASTING");
  assert.strictEqual(mapped.numericValue, 95.0);
  assert.strictEqual(mapped.isValid, true);
  assert.strictEqual(mapped.sampleId, "SMP-001");
});

test("AnalyzerMapper handles invalid or unmapped test results", () => {
  const mapper = new AnalyzerMapper(sampleMapping);

  const invalidParsed: ParsedResult = {
    sampleId: "SMP-002",
    testCode: "UNKNOWN_TEST",
    value: "INVALID",
    timestamp: new Date().toISOString(),
    rawMessageId: "msg-2",
  };

  const mapped = mapper.mapResult(invalidParsed);
  assert.strictEqual(mapped.standardTestCode, "UNKNOWN_TEST");
  assert.strictEqual(mapped.value, "INVALID");
  // Non-numeric text value when numbers expected or empty value handled
  assert.strictEqual(mapped.numericValue, undefined);
});
