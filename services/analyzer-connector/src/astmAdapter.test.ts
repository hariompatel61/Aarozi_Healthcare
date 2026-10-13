import test from "node:test";
import assert from "node:assert";
import { AstmAdapter } from "./astmAdapter.js";

const ASTM_FIXTURE = `H|^&|||Aeroset^1.0|||||||P|E1394-97|20261013120000
P|1||12345^^^PID1||Doe^John||19800101|M
O|1|SMP-001^^TestTray|1^1^1^1|^^^GLU
R|1|^^^GLU|98.5|mg/dL|70-100|N||F|||20261013120100
R|2|^^^CHOL|210.0|mg/dL|0-200|H||F|||20261013120105
L|1|N`;

test("AstmAdapter validation", () => {
  const adapter = new AstmAdapter();
  assert.strictEqual(adapter.getProtocolName(), "ASTM");
  assert.strictEqual(adapter.validate(ASTM_FIXTURE), true);
  assert.strictEqual(adapter.validate("invalid data without header"), false);
});

test("AstmAdapter parsing of test fixture", () => {
  const adapter = new AstmAdapter();
  const results = adapter.parse(ASTM_FIXTURE, "msg-astm-1");

  assert.strictEqual(results.length, 2);
  assert.strictEqual(results[0].sampleId, "SMP-001");
  assert.strictEqual(results[0].testCode, "GLU");
  assert.strictEqual(results[0].value, "98.5");
  assert.strictEqual(results[0].units, "mg/dL");
  assert.strictEqual(results[0].flags, "N");
  assert.strictEqual(results[0].rawMessageId, "msg-astm-1");

  assert.strictEqual(results[1].sampleId, "SMP-001");
  assert.strictEqual(results[1].testCode, "CHOL");
  assert.strictEqual(results[1].value, "210.0");
  assert.strictEqual(results[1].units, "mg/dL");
  assert.strictEqual(results[1].flags, "H");
});
