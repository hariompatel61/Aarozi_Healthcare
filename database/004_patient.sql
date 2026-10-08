CREATE TABLE IF NOT EXISTS patients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  branch_id uuid REFERENCES branches(id),
  patient_no text NOT NULL,
  first_name text NOT NULL,
  middle_name text,
  last_name text,
  date_of_birth date,
  sex text,
  mobile_normalized text,
  email text,
  blood_group text,
  abha_id text,
  address_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, patient_no)
);

CREATE INDEX IF NOT EXISTS idx_patients_mobile ON patients (tenant_id, mobile_normalized);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients (tenant_id, lower(last_name), lower(first_name));

CREATE TABLE IF NOT EXISTS patient_identifiers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  patient_id uuid NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
  identifier_type text NOT NULL,
  identifier_value text NOT NULL,
  is_primary boolean NOT NULL DEFAULT false,
  UNIQUE (tenant_id, identifier_type, identifier_value)
);
