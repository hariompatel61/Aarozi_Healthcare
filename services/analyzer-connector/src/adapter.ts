export interface ParsedResult {
  sampleId: string;
  testCode: string;
  value: string;
  units?: string;
  flags?: string;
  timestamp: string;
  rawMessageId: string;
}

export interface ProtocolAdapter {
  getProtocolName(): string;
  validate(rawPayload: string): boolean;
  parse(rawPayload: string, rawMessageId: string): ParsedResult[];
}

export class BaseAdapter implements ProtocolAdapter {
  protected protocolName: string;

  constructor(protocolName: string = "GENERIC") {
    this.protocolName = protocolName;
  }

  getProtocolName(): string {
    return this.protocolName;
  }

  validate(rawPayload: string): boolean {
    return typeof rawPayload === "string" && rawPayload.trim().length > 0;
  }

  parse(rawPayload: string, rawMessageId: string): ParsedResult[] {
    if (!this.validate(rawPayload)) {
      throw new Error(`Invalid raw payload for protocol ${this.protocolName}`);
    }
    return [];
  }
}
