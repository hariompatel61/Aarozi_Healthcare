import { ProtocolAdapter, ParsedResult } from "./adapter.js";

export class Hl7Adapter implements ProtocolAdapter {
  getProtocolName(): string {
    return "HL7";
  }

  validate(rawPayload: string): boolean {
    if (typeof rawPayload !== "string" || rawPayload.trim().length === 0) {
      return false;
    }
    return rawPayload.includes("MSH|") || rawPayload.includes("OBX|");
  }

  parse(rawPayload: string, rawMessageId: string): ParsedResult[] {
    if (!this.validate(rawPayload)) {
      throw new Error("Invalid HL7 payload format");
    }

    const lines = rawPayload.split(/\r?\n/);
    const results: ParsedResult[] = [];
    let currentSampleId = "UNKNOWN";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const fields = trimmed.split("|");
      const segmentId = fields[0];

      if (segmentId === "OBR" && fields.length > 3) {
        // OBR segment: OBR|1|PlacerOrder|FillerOrder|TestCode^TestDesc...
        currentSampleId = fields[2] || fields[3] || currentSampleId;
      } else if (segmentId === "OBX" && fields.length > 5) {
        // OBX segment: OBX|1|ST|GLU^Glucose|1|98.5|mg/dL|70-100|N|||F
        const observationId = fields[3] || "";
        const idParts = observationId.split("^");
        const testCode = idParts[0] || observationId;
        const value = fields[5] || "";
        const units = fields[6] || undefined;
        const flags = fields[8] || undefined;

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
