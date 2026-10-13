export interface StoredMessage {
  id: string;
  tenantId: string;
  analyzerId: string;
  receivedAt: string;
  rawPayload: string;
  parseStatus: "received" | "parsed" | "error";
  errorMessage?: string;
}

export class RawMessageStorage {
  private messages: StoredMessage[] = [];

  save(message: Omit<StoredMessage, "id" | "receivedAt">): StoredMessage {
    const record: StoredMessage = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      tenantId: message.tenantId,
      analyzerId: message.analyzerId,
      receivedAt: new Date().toISOString(),
      rawPayload: message.rawPayload,
      parseStatus: message.parseStatus,
      errorMessage: message.errorMessage,
    };
    this.messages.push(record);
    return record;
  }

  findByTenant(tenantId: string): StoredMessage[] {
    return this.messages.filter((m) => m.tenantId === tenantId);
  }

  findById(id: string): StoredMessage | undefined {
    return this.messages.find((m) => m.id === id);
  }

  updateStatus(id: string, parseStatus: "received" | "parsed" | "error", errorMessage?: string): boolean {
    const msg = this.findById(id);
    if (!msg) return false;
    msg.parseStatus = parseStatus;
    if (errorMessage !== undefined) {
      msg.errorMessage = errorMessage;
    }
    return true;
  }
}

export const defaultStorage = new RawMessageStorage();
