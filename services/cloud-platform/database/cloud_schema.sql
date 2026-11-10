-- ============================================================================
-- AAROZI HEALTHCARE — HOSTED CLOUD PLATFORM DATABASE SCHEMA
-- Target Engine: PostgreSQL 14+ (Supabase / Neon / Railway / AWS RDS / Vercel)
-- Purpose: Houses only commercial SaaS operations (Labs, Plans, Licenses, Payments, CMS)
-- NOTE: Contains ZERO patient health data. Clinical data stays 100% on the lab PC.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. PLATFORM SUPER ADMIN USERS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS platform_admins (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'SUPER_ADMIN' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. SUBSCRIPTION PLANS MASTER
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscription_plans (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    code VARCHAR(50) UNIQUE NOT NULL,              -- e.g. 'YEARLY_PRO', 'LIFETIME_COMMERCIAL'
    name VARCHAR(255) NOT NULL,
    billing_cycle VARCHAR(50) NOT NULL,            -- 'monthly', 'annual', 'one_time'
    base_price_inr NUMERIC(12, 2) NOT NULL,
    duration_days INT NOT NULL,                    -- 365 for annual, 36500 for lifetime
    grace_days INT DEFAULT 30 NOT NULL,
    max_workstations INT DEFAULT 10 NOT NULL,
    is_lifetime BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    features_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 3. TENANT LABORATORIES (CUSTOMERS)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenant_laboratories (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    lab_name VARCHAR(255) NOT NULL,
    owner_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    gstin VARCHAR(50),
    status VARCHAR(50) DEFAULT 'ACTIVE' NOT NULL,  -- 'ACTIVE', 'TRIAL', 'SUSPENDED', 'EXPIRED'
    plan_code VARCHAR(50) REFERENCES subscription_plans(code) ON DELETE RESTRICT,
    hardware_fingerprint VARCHAR(255),             -- Workstation hardware lock
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. ISSUED CRYPTOGRAPHIC LICENSES (ED25519)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS issued_licenses (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    license_key VARCHAR(100) UNIQUE NOT NULL,      -- e.g. 'LIC-PROD-20261111-89F2'
    lab_id VARCHAR(36) REFERENCES tenant_laboratories(id) ON DELETE CASCADE,
    plan_code VARCHAR(50) REFERENCES subscription_plans(code) ON DELETE RESTRICT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    grace_until TIMESTAMPTZ NOT NULL,
    hardware_fingerprint VARCHAR(255),
    signing_key_id VARCHAR(100) DEFAULT 'aarozi-root-key-2026' NOT NULL,
    signing_algorithm VARCHAR(50) DEFAULT 'Ed25519' NOT NULL,
    signature_hex TEXT NOT NULL,
    license_payload_json JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'ACTIVE' NOT NULL,  -- 'ACTIVE', 'REVOKED', 'EXPIRED'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 5. PAYMENT & BILLING TRANSACTIONS (RAZORPAY)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment_transactions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    gateway_order_id VARCHAR(100),
    gateway_payment_id VARCHAR(100),
    lab_id VARCHAR(36) REFERENCES tenant_laboratories(id) ON DELETE SET NULL,
    plan_code VARCHAR(50) REFERENCES subscription_plans(code),
    amount_inr NUMERIC(12, 2) NOT NULL,
    taxable_amount_inr NUMERIC(12, 2) NOT NULL,
    gst_rate_percent NUMERIC(5, 2) DEFAULT 18.0 NOT NULL,
    gst_amount_inr NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR' NOT NULL,
    payment_method VARCHAR(50),                    -- 'upi', 'card', 'netbanking'
    payment_status VARCHAR(50) DEFAULT 'pending' NOT NULL, -- 'pending', 'paid', 'failed', 'refunded'
    invoice_number VARCHAR(100) UNIQUE,
    paid_at TIMESTAMPTZ,
    raw_webhook_event JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 6. DESKTOP RELEASES & INSTALLER DOWNLOADS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS desktop_releases (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    version VARCHAR(50) UNIQUE NOT NULL,           -- e.g. 'v2.4.0'
    release_title VARCHAR(255) NOT NULL,
    release_notes TEXT NOT NULL,
    download_url TEXT NOT NULL,
    file_size_mb NUMERIC(6, 2) NOT NULL,
    sha256_checksum VARCHAR(128) NOT NULL,
    is_latest BOOLEAN DEFAULT FALSE NOT NULL,
    is_mandatory BOOLEAN DEFAULT FALSE NOT NULL,
    published_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 7. CMS BLOG ARTICLES (PUBLIC FACING)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cms_blog_posts (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    excerpt TEXT NOT NULL,
    content_markdown TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,                -- 'Pathology', 'NABL Compliance', 'Business', 'Technology'
    author_name VARCHAR(100) DEFAULT 'Aarozi Clinical Team' NOT NULL,
    read_time_minutes INT DEFAULT 5 NOT NULL,
    is_published BOOLEAN DEFAULT TRUE NOT NULL,
    published_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_tenant_labs_email ON tenant_laboratories(email);
CREATE INDEX IF NOT EXISTS idx_tenant_labs_status ON tenant_laboratories(status);
CREATE INDEX IF NOT EXISTS idx_licenses_lab ON issued_licenses(lab_id);
CREATE INDEX IF NOT EXISTS idx_licenses_status ON issued_licenses(status);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON payment_transactions(payment_status);
CREATE INDEX IF NOT EXISTS idx_transactions_order ON payment_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_blog_slug ON cms_blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_blog_published ON cms_blog_posts(is_published);

