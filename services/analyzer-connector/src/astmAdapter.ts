import { ProtocolAdapter, ParsedResult } from "./adapter.js";

export class AstmAdapter implements ProtocolAdapter {
  getProtocolName(): string {
    return "ASTM";
  }

  validate(rawPayload: string): boolean {
    if (typeof rawPayload !== "string" || rawPayload.trim().length === 0) {
      return false;
    }
    return rawPayload.includes("H|") || rawPayload.includes("R|");
  }

  parse(rawPayload: string, rawMessageId: string): ParsedResult[] {
    if (!this.validate(rawPayload)) {
      throw new Error("Invalid ASTM payload format");
    }

    const lines = rawPayload.split(/\r?\n/);
    const results: ParsedResult[] = [];
    let currentSampleId = "UNKNOWN";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const fields = trimmed.split("|");
      const recordType = fields[0];

      if (recordType === "O" && fields.length > 2) {
        const rawSample = fields[2] || fields[3] || currentSampleId;
        currentSampleId = rawSample.split("^")[0] || rawSample;
      } else if (recordType === "R" && fields.length > 3) {
        const testField = fields[2] || "";
        const testCodeParts = testField.split("^");
        const testCode = testCodeParts[testCodeParts.length - 1] || testField;
        const value = fields[3] || "";
        const units = fields[4] || undefined;
        const flags = fields[6] || undefined;

        results.push({
          sampleId: currentSampleId,
          testCode,
          value,
          units,
          flags,
          timestamp: new Date().toISOString(),
          rawMessageId,
        });
      }
    }

    return results;
  }
}

