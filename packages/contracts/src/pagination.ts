/**
 * Cursor-based pagination contract (no OFFSET queries).
 */
export interface PaginatedResponse<T> {
  ok: true;
  data: T[];
  total?: number | null;
  next_cursor?: string | null;
  page_size: number;
}