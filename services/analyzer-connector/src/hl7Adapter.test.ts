import test from "node:test";
import assert from "node:assert";
import { Hl7Adapter } from "./hl7Adapter.js";

const HL7_FIXTURE = `MSH|^~\\&|LIMS|Lab1|Aarozi|Hospital|20261013120000||ORU^R01|MSG0001|P|2.5
PID|1||12345^^^MR^MR||Doe^John||19800101|M
OBR|1|ORD123|FILL123|CBC^Complete Blood Count|||20261013120000
OBX|1|NM|WBC^White Blood Cells|1|7.5|10^3/uL|4.0-11.0|N|||F
OBX|2|NM|RBC^Red Blood Cells|1|4.8|10^6/uL|4.2-5.9|N|||F`;

test("Hl7Adapter validation", () => {
  const adapter = new Hl7Adapter();
  assert.strictEqual(adapter.getProtocolName(), "HL7");
  assert.strictEqual(adapter.validate(HL7_FIXTURE), true);
  assert.strictEqual(adapter.validate("invalid hl7 message"), false);
});

test("Hl7Adapter parsing of controlled HL7 fixture", () => {
  const adapter = new Hl7Adapter();
  const results = adapter.parse(HL7_FIXTURE, "msg-hl7-1");

  assert.strictEqual(results.length, 2);
  assert.strictEqual(results[0].sampleId, "ORD123");
  assert.strictEqual(results[0].testCode, "WBC");
  assert.strictEqual(results[0].value, "7.5");
  assert.strictEqual(results[0].units, "10^3/uL");
  assert.strictEqual(results[0].flags, "N");
  assert.strictEqual(results[0].rawMessageId, "msg-hl7-1");

  assert.strictEqual(results[1].sampleId, "ORD123");
  assert.strictEqual(results[1].testCode, "RBC");
  assert.strictEqual(results[1].value, "4.8");
  assert.strictEqual(results[1].units, "10^6/uL");
});
