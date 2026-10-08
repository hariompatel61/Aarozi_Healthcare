CREATE TABLE IF NOT EXISTS referral_partners (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  partner_type text NOT NULL,
  name text NOT NULL,
  phone text,
  email text,
  status text NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS referral_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  partner_id uuid NOT NULL REFERENCES referral_partners(id),
  scope_type text NOT NULL,
  scope_id uuid,
  effective_from timestamptz NOT NULL,
  effective_to timestamptz,
  patient_discount_pct numeric(7,4) NOT NULL DEFAULT 0,
  commission_pct numeric(7,4) NOT NULL DEFAULT 0,
  commission_fixed numeric(14,2),
  priority integer NOT NULL DEFAULT 100,
  status text NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS invoices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  branch_id uuid REFERENCES branches(id),
  patient_id uuid NOT NULL REFERENCES patients(id),
  invoice_no text NOT NULL,
  status text NOT NULL DEFAULT 'issued',
  subtotal numeric(14,2) NOT NULL DEFAULT 0,
  discount_total numeric(14,2) NOT NULL DEFAULT 0,
  tax_total numeric(14,2) NOT NULL DEFAULT 0,
  grand_total numeric(14,2) NOT NULL DEFAULT 0,
  UNIQUE (tenant_id, invoice_no)
);

CREATE TABLE IF NOT EXISTS invoice_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  invoice_id uuid NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
  order_item_id uuid REFERENCES order_items(id),
  description text NOT NULL,
  qty numeric(14,3) NOT NULL DEFAULT 1,
  unit_price numeric(14,2) NOT NULL DEFAULT 0,
  discount numeric(14,2) NOT NULL DEFAULT 0,
  tax numeric(14,2) NOT NULL DEFAULT 0,
  line_total numeric(14,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS payments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  invoice_id uuid NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
  amount numeric(14,2) NOT NULL CHECK (amount >= 0),
  method text NOT NULL,
  provider_reference text,
  received_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS commission_ledger (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  referral_partner_id uuid NOT NULL REFERENCES referral_partners(id),
  invoice_id uuid REFERENCES invoices(id),
  amount numeric(14,2) NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'pending',
  calculated_at timestamptz NOT NULL DEFAULT now(),
  settled_at timestamptz
);
