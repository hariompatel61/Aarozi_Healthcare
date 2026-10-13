/**
 * Standard error contract matching Python API ErrorResponse & ErrorDetail.
 */
export interface ErrorDetail {
  code: string;
  message: string;
  field?: string | null;
}

export interface ErrorResponse {
  ok: false;
  error: ErrorDetail;
}