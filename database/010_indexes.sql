CREATE INDEX IF NOT EXISTS idx_order_queue ON patients_orders (tenant_id, branch_id, status, ordered_at DESC);
CREATE INDEX IF NOT EXISTS idx_sample_queue ON samples (tenant_id, status, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_result_queue ON results (tenant_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_invoice_patient ON invoices (tenant_id, patient_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments (invoice_id, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs (tenant_id, entity_type, entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_queue ON sync_events (tenant_id, status, created_at);
