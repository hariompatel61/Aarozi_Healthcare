-- 013_integrations.sql: External SaaS, messaging, and cloud storage integration settings
CREATE TABLE IF NOT EXISTS integration_configs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  category text NOT NULL, -- whatsapp, google_drive, sms, email
  provider text NOT NULL DEFAULT 'default', -- meta_cloud_api, direct_web, google_drive, msg91, smtp
  is_enabled boolean NOT NULL DEFAULT false,
  config_json text NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, category)
);

CREATE INDEX IF NOT EXISTS ix_integration_configs_tenant ON integration_configs(tenant_id, category);

