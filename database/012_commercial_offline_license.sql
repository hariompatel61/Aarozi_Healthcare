-- Aarozi Healthcare commercial offline-first licensing and resumable sync.

ALTER TABLE licenses
  ADD COLUMN IF NOT EXISTS installation_id uuid,
  ADD COLUMN IF NOT EXISTS plan_code text,
  ADD COLUMN IF NOT EXISTS signature_algorithm text,
  ADD COLUMN IF NOT EXISTS signing_key_id text,
  ADD COLUMN IF NOT EXISTS signed_payload_json jsonb,
  ADD COLUMN IF NOT EXISTS signature text,
  ADD COLUMN IF NOT EXISTS issued_at timestamptz,
  ADD COLUMN IF NOT EXISTS last_trusted_time timestamptz,
  ADD COLUMN IF NOT EXISTS clock_rollback_detected_at timestamptz,
  ADD COLUMN IF NOT EXISTS revocation_reason text;

CREATE TABLE IF NOT EXISTS offline_activation_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  installation_id uuid NOT NULL,
  request_nonce text NOT NULL UNIQUE,
  request_payload_json jsonb NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  requested_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz
);

CREATE TABLE IF NOT EXISTS license_renewal_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  installation_id uuid NOT NULL,
  request_nonce text NOT NULL UNIQUE,
  current_license_id uuid REFERENCES licenses(id),
  request_payload_json jsonb NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  requested_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz
);

CREATE TABLE IF NOT EXISTS sync_checkpoints (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  device_id uuid REFERENCES devices(id),
  stream_name text NOT NULL,
  last_acked_sequence bigint NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'active',
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, device_id, stream_name)
);

CREATE INDEX IF NOT EXISTS idx_licenses_tenant_status_valid_to
  ON licenses (tenant_id, status, valid_to);

CREATE INDEX IF NOT EXISTS idx_activation_requests_tenant_status
  ON offline_activation_requests (tenant_id, status, requested_at);

CREATE INDEX IF NOT EXISTS idx_renewal_requests_tenant_status
  ON license_renewal_requests (tenant_id, status, requested_at);

CREATE INDEX IF NOT EXISTS idx_sync_checkpoints_tenant_device
  ON sync_checkpoints (tenant_id, device_id, stream_name);
