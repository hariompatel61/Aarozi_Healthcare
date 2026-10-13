export interface SampleRecord {
  sampleId: string;
  patientId: string;
  orderId: string;
  status: "collected" | "received" | "processed" | "rejected";
  testCodes: string[];
}

export interface MatchResult {
  sampleId: string;
  matched: boolean;
  sampleRecord?: SampleRecord;
  rejectionReason?: string;
}

export class SampleMatcher {
  private registry: Map<string, SampleRecord> = new Map();

  registerSample(sample: SampleRecord) {
    this.registry.set(sample.sampleId, sample);
  }

  registerSamples(samples: SampleRecord[]) {
    for (const s of samples) {
      this.registerSample(s);
    }
  }

  matchSample(sampleId: string): MatchResult {
    if (!sampleId || sampleId.trim() === "" || sampleId === "UNKNOWN") {
      return {
        sampleId: sampleId || "UNKNOWN",
        matched: false,
        rejectionReason: "Missing or invalid sample identifier",
      };
    }

    const record = this.registry.get(sampleId);
    if (!record) {
      return {
        sampleId,
        matched: false,
        rejectionReason: `Sample ID ${sampleId} not found in pending order registry (safe rejection)`,
      };
    }

    if (record.status === "rejected") {
      return {
        sampleId,
        matched: false,
        sampleRecord: record,
        rejectionReason: `Sample ID ${sampleId} was previously rejected`,
      };
    }

    return {
      sampleId,
      matched: true,
      sampleRecord: record,
    };
  }
}
