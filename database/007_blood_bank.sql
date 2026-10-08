CREATE TABLE IF NOT EXISTS donors (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  donor_no text NOT NULL,
  patient_id uuid REFERENCES patients(id),
  abha_id text,
  status text NOT NULL DEFAULT 'active',
  UNIQUE (tenant_id, donor_no)
);

CREATE TABLE IF NOT EXISTS donations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  donor_id uuid NOT NULL REFERENCES donors(id),
  donated_at timestamptz NOT NULL DEFAULT now(),
  screening_status text NOT NULL DEFAULT 'pending',
  eligibility_status text NOT NULL DEFAULT 'pending',
  deferral_reason text
);

CREATE TABLE IF NOT EXISTS blood_units (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  donation_id uuid REFERENCES donations(id),
  unit_no text NOT NULL,
  component_type text NOT NULL,
  blood_group text,
  status text NOT NULL DEFAULT 'collected',
  expiry_at timestamptz,
  storage_location text,
  UNIQUE (tenant_id, unit_no)
);

CREATE INDEX IF NOT EXISTS idx_blood_stock ON blood_units (tenant_id, blood_group, component_type, status, expiry_at);

CREATE TABLE IF NOT EXISTS blood_unit_tests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  blood_unit_id uuid NOT NULL REFERENCES blood_units(id) ON DELETE RESTRICT,
  test_code text NOT NULL,
  result text,
  status text NOT NULL DEFAULT 'pending',
  verified_by uuid REFERENCES users(id),
  verified_at timestamptz
);

CREATE TABLE IF NOT EXISTS cross_matches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  patient_id uuid NOT NULL REFERENCES patients(id),
  blood_unit_id uuid NOT NULL REFERENCES blood_units(id),
  compatibility_status text NOT NULL DEFAULT 'pending',
  performed_by uuid REFERENCES users(id),
  approved_by uuid REFERENCES users(id),
  performed_at timestamptz,
  approved_at timestamptz
);

CREATE TABLE IF NOT EXISTS blood_movements (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  blood_unit_id uuid NOT NULL REFERENCES blood_units(id),
  movement_type text NOT NULL,
  from_status text,
  to_status text NOT NULL,
  patient_id uuid REFERENCES patients(id),
  reason text,
  actor_user_id uuid REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now()
);
