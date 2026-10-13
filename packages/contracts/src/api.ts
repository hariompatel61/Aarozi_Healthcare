/**
 * Standard success API response envelope.
 */
export interface APIResponse<T> {
  ok: true;
  data: T;
}