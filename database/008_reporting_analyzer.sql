CREATE TABLE IF NOT EXISTS report_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid,
  name text NOT NULL,
  category text,
  version integer NOT NULL DEFAULT 1,
  is_global boolean NOT NULL DEFAULT false,
  status text NOT NULL DEFAULT 'draft',
  schema_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  patient_id uuid NOT NULL REFERENCES patients(id),
  result_id uuid REFERENCES results(id),
  report_no text NOT NULL,
  template_id uuid REFERENCES report_templates(id),
  version integer NOT NULL DEFAULT 1,
  status text NOT NULL DEFAULT 'draft',
  released_at timestamptz,
  qr_token text,
  UNIQUE (tenant_id, report_no)
);

CREATE TABLE IF NOT EXISTS analyzers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  branch_id uuid REFERENCES branches(id),
  name text NOT NULL,
  protocol text NOT NULL,
  connection_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  mapping_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS analyzer_messages (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  analyzer_id uuid NOT NULL REFERENCES analyzers(id),
  received_at timestamptz NOT NULL DEFAULT now(),
  raw_payload text NOT NULL,
  parse_status text NOT NULL DEFAULT 'received',
  error_message text
);
