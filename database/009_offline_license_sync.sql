CREATE TABLE IF NOT EXISTS licenses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  license_key_hash text NOT NULL UNIQUE,
  mode text NOT NULL,
  status text NOT NULL DEFAULT 'active',
  valid_from timestamptz NOT NULL,
  valid_to timestamptz NOT NULL,
  grace_until timestamptz,
  entitlements_json jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS devices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  device_code text NOT NULL,
  device_type text NOT NULL,
  last_seen_at timestamptz,
  status text NOT NULL DEFAULT 'active',
  UNIQUE (tenant_id, device_code)
);

CREATE TABLE IF NOT EXISTS sync_events (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  device_id uuid REFERENCES devices(id),
  entity_type text NOT NULL,
  entity_id uuid NOT NULL,
  operation text NOT NULL,
  payload_hash text NOT NULL,
  payload_json jsonb NOT NULL,
  version integer NOT NULL,
  status text NOT NULL DEFAULT 'queued',
  created_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz
);

CREATE TABLE IF NOT EXISTS sync_conflicts (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  sync_event_id bigint REFERENCES sync_events(id),
  entity_type text NOT NULL,
  entity_id uuid NOT NULL,
  resolution_status text NOT NULL DEFAULT 'open',
  local_payload jsonb,
  remote_payload jsonb,
  resolution_notes text,
  resolved_by uuid REFERENCES users(id),
  resolved_at timestamptz
);
