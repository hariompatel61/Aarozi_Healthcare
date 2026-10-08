CREATE TABLE IF NOT EXISTS tests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  code text NOT NULL,
  display_name text NOT NULL,
  department_id uuid REFERENCES departments(id),
  specimen_type text,
  container_type text,
  method text,
  unit text,
  decimal_precision smallint NOT NULL DEFAULT 2,
  analyzer_code text,
  loinc_code text,
  calculation_formula text,
  status text NOT NULL DEFAULT 'active',
  UNIQUE (tenant_id, code)
);

CREATE TABLE IF NOT EXISTS test_reference_ranges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id uuid NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
  sex text,
  age_min numeric,
  age_max numeric,
  low_value numeric,
  high_value numeric,
  critical_low numeric,
  critical_high numeric,
  text_range text,
  effective_from timestamptz NOT NULL DEFAULT now(),
  effective_to timestamptz
);

CREATE TABLE IF NOT EXISTS orders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  branch_id uuid REFERENCES branches(id),
  patient_id uuid NOT NULL REFERENCES patients(id),
  order_no text NOT NULL,
  status text NOT NULL DEFAULT 'ordered',
  referral_partner_id uuid,
  ordered_at timestamptz NOT NULL DEFAULT now(),
  created_by uuid REFERENCES users(id),
  UNIQUE (tenant_id, order_no)
);

CREATE TABLE IF NOT EXISTS order_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id uuid NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
  test_id uuid NOT NULL REFERENCES tests(id),
  profile_name text,
  package_name text,
  status text NOT NULL DEFAULT 'ordered',
  price numeric(14,2) NOT NULL DEFAULT 0,
  discount numeric(14,2) NOT NULL DEFAULT 0,
  tax numeric(14,2) NOT NULL DEFAULT 0,
  final_amount numeric(14,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS samples (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  order_item_id uuid NOT NULL REFERENCES order_items(id) ON DELETE RESTRICT,
  barcode text NOT NULL,
  specimen_type text,
  collected_at timestamptz,
  received_at timestamptz,
  status text NOT NULL DEFAULT 'ordered',
  rejection_reason text,
  UNIQUE (tenant_id, barcode)
);

CREATE TABLE IF NOT EXISTS results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  order_item_id uuid NOT NULL REFERENCES order_items(id) ON DELETE RESTRICT,
  version integer NOT NULL DEFAULT 1,
  status text NOT NULL DEFAULT 'draft',
  verified_by uuid REFERENCES users(id),
  verified_at timestamptz,
  approved_by uuid REFERENCES users(id),
  approved_at timestamptz,
  amendment_reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (order_item_id, version)
);

CREATE TABLE IF NOT EXISTS result_values (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  result_id uuid NOT NULL REFERENCES results(id) ON DELETE CASCADE,
  analyte_code text NOT NULL,
  raw_value text,
  numeric_value numeric,
  unit text,
  reference_text text,
  abnormal_flag text,
  critical_flag boolean NOT NULL DEFAULT false
);
