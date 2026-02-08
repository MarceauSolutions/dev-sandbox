-- MCP Aggregator Platform - PostgreSQL Schema
-- Version: 1.0.0
-- Created: 2026-01-12
--
-- This schema supports the Universal MCP Aggregation Platform:
-- - MCP Registry (discovery, registration, health tracking)
-- - Routing Engine (scoring, selection, circuit breaker state)
-- - Billing System (transactions, fees, payouts)
-- - Rate Cards (rideshare pricing data)

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- ENUM TYPES
-- ============================================

CREATE TYPE mcp_status AS ENUM ('active', 'inactive', 'suspended', 'pending_review');
CREATE TYPE mcp_category AS ENUM (
    'rideshare', 'flights', 'hotels', 'restaurants',
    'food_delivery', 'events', 'shopping', 'finance',
    'healthcare', 'utilities', 'other'
);
CREATE TYPE connectivity_type AS ENUM (
    'http',      -- Standard REST API (default)
    'email',     -- SMTP-based (send email, await response)
    'oauth',     -- OAuth2 with token refresh
    'webhook',   -- Inbound (they call us)
    'graphql',   -- GraphQL queries
    'async'      -- Long-running (hours/days)
);
CREATE TYPE transaction_status AS ENUM ('pending', 'completed', 'failed', 'refunded');
CREATE TYPE payout_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE circuit_state AS ENUM ('closed', 'open', 'half_open');
CREATE TYPE pricing_model AS ENUM (
    'per_request',   -- Traditional pay-per-call (default)
    'subscription',  -- Monthly fee, unlimited calls
    'commission',    -- Percentage of transaction value
    'tiered',        -- Volume-based pricing with discount tiers
    'hybrid'         -- Base subscription + per-request charges
);

-- ============================================
-- CORE TABLES
-- ============================================

-- MCP Developers (who build and maintain MCPs)
CREATE TABLE developers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    display_name VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,  -- bcrypt hashed API key
    stripe_customer_id VARCHAR(255),
    stripe_account_id VARCHAR(255),  -- For payouts
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

-- MCP Registry (all registered MCPs)
CREATE TABLE mcps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    developer_id UUID REFERENCES developers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,  -- URL-safe identifier
    description TEXT,
    category mcp_category NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',

    -- Connectivity (determines how we communicate with this MCP)
    connectivity_type connectivity_type DEFAULT 'http',  -- How to connect
    endpoint_url VARCHAR(500),  -- HTTP URL (required for http/oauth/graphql)
    email_address VARCHAR(255),  -- Email address (required for email type)
    webhook_path VARCHAR(255),  -- Our path for webhooks (required for webhook type)

    health_check_url VARCHAR(500),
    documentation_url VARCHAR(500),

    -- Pricing
    pricing_model pricing_model DEFAULT 'per_request',  -- How this MCP bills
    fee_per_request DECIMAL(10, 4) DEFAULT 0.01,  -- What we charge AI platforms (per_request/hybrid)
    developer_share DECIMAL(5, 4) DEFAULT 0.80,   -- Developer gets 80% (configurable per-MCP)
    commission_rate DECIMAL(5, 4),  -- Commission rate for commission model (e.g., 0.10 = 10%)
    subscription_fee DECIMAL(10, 2),  -- Monthly subscription fee (subscription/hybrid models)

    -- Status & Quality
    status mcp_status DEFAULT 'pending_review',
    avg_response_time_ms INTEGER DEFAULT 0,
    avg_rating DECIMAL(3, 2) DEFAULT 0.00,
    total_requests BIGINT DEFAULT 0,
    total_errors BIGINT DEFAULT 0,
    uptime_percent DECIMAL(5, 2) DEFAULT 100.00,

    -- Metadata
    tags TEXT[],  -- ['realtime', 'geolocation', 'pricing']
    supported_regions TEXT[],  -- ['us', 'eu', 'global']
    rate_limit_rpm INTEGER DEFAULT 100,  -- Requests per minute
    timeout_ms INTEGER DEFAULT 30000,  -- Max allowed timeout

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_health_check TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_developer_share CHECK (developer_share >= 0 AND developer_share <= 1)
);

-- MCP Capabilities (what actions/queries each MCP supports)
CREATE TABLE mcp_capabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID REFERENCES mcps(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,  -- 'compare_prices', 'book_ride', etc.
    description TEXT,
    input_schema JSONB,  -- JSON Schema for input validation
    output_schema JSONB,  -- JSON Schema for output format
    examples JSONB,  -- Example inputs/outputs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(mcp_id, name)
);

-- Health Check History
CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID REFERENCES mcps(id) ON DELETE CASCADE,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_healthy BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,

    -- Index for recent checks lookup
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Circuit Breaker State (for fault tolerance)
CREATE TABLE circuit_breaker_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID REFERENCES mcps(id) ON DELETE CASCADE UNIQUE,
    state circuit_state DEFAULT 'closed',
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    half_opened_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- BILLING TABLES
-- ============================================

-- AI Platform Clients (Claude, ChatGPT, etc.)
CREATE TABLE ai_platforms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    billing_email VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    monthly_credit_limit DECIMAL(12, 2) DEFAULT 1000.00,
    current_balance DECIMAL(12, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transactions (every API call that costs money)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Who made the request
    ai_platform_id UUID REFERENCES ai_platforms(id),

    -- Which MCP handled it
    mcp_id UUID REFERENCES mcps(id),
    developer_id UUID REFERENCES developers(id),

    -- Request details
    request_id VARCHAR(255) UNIQUE NOT NULL,  -- Idempotency key
    capability_name VARCHAR(255),
    request_payload JSONB,
    response_payload JSONB,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    response_time_ms INTEGER,

    -- Billing
    gross_amount DECIMAL(10, 4) NOT NULL,  -- Total charged to AI platform
    platform_fee DECIMAL(10, 4) NOT NULL,  -- Our cut (configurable per-MCP)
    developer_payout DECIMAL(10, 4) NOT NULL,  -- Developer's cut (configurable per-MCP)

    -- Pricing Model (supports multiple billing strategies)
    pricing_model pricing_model DEFAULT 'per_request',  -- How this transaction was billed
    subscription_id VARCHAR(255),  -- Reference to active subscription (subscription/hybrid)
    booking_value DECIMAL(12, 4),  -- Original transaction value (commission model)
    commission_rate DECIMAL(5, 4),  -- Commission rate applied (commission model)
    tier_name VARCHAR(50),  -- Tier applied (tiered model, e.g., 'starter', 'enterprise')

    -- Status
    status transaction_status DEFAULT 'pending',
    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily Aggregated Stats (for dashboards and billing)
CREATE TABLE daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,

    -- Can be per-MCP or per-platform
    mcp_id UUID REFERENCES mcps(id),
    ai_platform_id UUID REFERENCES ai_platforms(id),
    developer_id UUID REFERENCES developers(id),

    -- Metrics
    total_requests BIGINT DEFAULT 0,
    successful_requests BIGINT DEFAULT 0,
    failed_requests BIGINT DEFAULT 0,
    avg_response_time_ms INTEGER DEFAULT 0,
    p95_response_time_ms INTEGER DEFAULT 0,
    p99_response_time_ms INTEGER DEFAULT 0,

    -- Revenue
    gross_revenue DECIMAL(12, 4) DEFAULT 0,
    platform_revenue DECIMAL(12, 4) DEFAULT 0,
    developer_revenue DECIMAL(12, 4) DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(date, mcp_id, ai_platform_id)
);

-- Developer Payouts
CREATE TABLE payouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    developer_id UUID REFERENCES developers(id),

    -- Amount
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Period covered
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Status
    status payout_status DEFAULT 'pending',
    stripe_transfer_id VARCHAR(255),
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Invoices (for AI platforms)
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_platform_id UUID REFERENCES ai_platforms(id),

    -- Billing period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Amount
    subtotal DECIMAL(12, 2) NOT NULL,
    tax DECIMAL(12, 2) DEFAULT 0,
    total DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Status
    status VARCHAR(50) DEFAULT 'draft',  -- draft, sent, paid, overdue
    due_date DATE,
    paid_at TIMESTAMP WITH TIME ZONE,
    stripe_invoice_id VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- RIDESHARE RATE CARDS (Flagship MCP Data)
-- ============================================

CREATE TABLE rate_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city VARCHAR(100) NOT NULL,
    service VARCHAR(50) NOT NULL,  -- 'uber', 'lyft'
    ride_type VARCHAR(50) NOT NULL,  -- 'uberx', 'lyft', 'uber_xl', etc.

    -- Pricing components
    base_fare DECIMAL(6, 2) NOT NULL,
    cost_per_mile DECIMAL(6, 2) NOT NULL,
    cost_per_minute DECIMAL(6, 2) NOT NULL,
    booking_fee DECIMAL(6, 2) NOT NULL,
    min_fare DECIMAL(6, 2) NOT NULL,

    -- Metadata
    source_url VARCHAR(500),  -- Where we got the data
    effective_date DATE NOT NULL,
    expires_date DATE,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(city, service, ride_type, effective_date)
);

-- Surge History (for ML model training)
CREATE TABLE surge_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city VARCHAR(100) NOT NULL,
    service VARCHAR(50) NOT NULL,
    ride_type VARCHAR(50),

    -- When
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    day_of_week SMALLINT NOT NULL,  -- 0=Monday, 6=Sunday
    hour_of_day SMALLINT NOT NULL,  -- 0-23

    -- Surge data
    surge_multiplier DECIMAL(4, 2) NOT NULL,
    is_predicted BOOLEAN DEFAULT FALSE,  -- True if from our model, False if observed
    confidence DECIMAL(4, 2),

    -- Context
    weather_condition VARCHAR(50),
    special_event VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- SUBSCRIPTIONS & PRICING TIERS
-- ============================================

-- Subscriptions (for subscription/hybrid pricing models)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_platform_id UUID REFERENCES ai_platforms(id) ON DELETE CASCADE,
    mcp_id UUID REFERENCES mcps(id) ON DELETE CASCADE,

    -- Subscription details
    plan_name VARCHAR(100) NOT NULL,  -- e.g., 'basic', 'pro', 'enterprise'
    monthly_fee DECIMAL(10, 2) NOT NULL,  -- Monthly subscription cost
    included_requests INTEGER,  -- Requests included (NULL = unlimited)

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, cancelled, expired
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,

    -- Stripe integration
    stripe_subscription_id VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(ai_platform_id, mcp_id, status)  -- One active subscription per platform/MCP
);

-- Pricing Tiers (for tiered pricing model)
CREATE TABLE pricing_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_id UUID REFERENCES mcps(id) ON DELETE CASCADE,

    -- Tier definition
    name VARCHAR(50) NOT NULL,  -- e.g., 'starter', 'growth', 'scale', 'enterprise'
    min_requests INTEGER NOT NULL DEFAULT 0,  -- Minimum requests for this tier
    max_requests INTEGER,  -- Maximum requests (NULL = unlimited)
    fee_per_request DECIMAL(10, 4) NOT NULL,  -- Price per request at this tier
    developer_share DECIMAL(5, 4) DEFAULT 0.80,  -- Developer share at this tier

    -- Order for tier selection (lower = first to check)
    tier_order INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(mcp_id, name),
    CONSTRAINT valid_tier_developer_share CHECK (developer_share >= 0 AND developer_share <= 1)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- MCP lookup
CREATE INDEX idx_mcps_category ON mcps(category);
CREATE INDEX idx_mcps_pricing_model ON mcps(pricing_model);
CREATE INDEX idx_mcps_status ON mcps(status);
CREATE INDEX idx_mcps_developer ON mcps(developer_id);
CREATE INDEX idx_mcps_slug ON mcps(slug);
CREATE INDEX idx_mcps_tags ON mcps USING GIN(tags);
CREATE INDEX idx_mcps_connectivity_type ON mcps(connectivity_type);

-- Capability search
CREATE INDEX idx_capabilities_mcp ON mcp_capabilities(mcp_id);
CREATE INDEX idx_capabilities_name ON mcp_capabilities(name);

-- Health checks (recent lookups)
CREATE INDEX idx_health_checks_mcp_time ON health_checks(mcp_id, checked_at DESC);

-- Transactions (billing queries)
CREATE INDEX idx_transactions_platform ON transactions(ai_platform_id, created_at DESC);
CREATE INDEX idx_transactions_mcp ON transactions(mcp_id, created_at DESC);
CREATE INDEX idx_transactions_developer ON transactions(developer_id, created_at DESC);
CREATE INDEX idx_transactions_request_id ON transactions(request_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_date ON transactions(created_at DESC);
CREATE INDEX idx_transactions_pricing_model ON transactions(pricing_model);
CREATE INDEX idx_transactions_subscription ON transactions(subscription_id) WHERE subscription_id IS NOT NULL;

-- Subscriptions (lookup active subscriptions)
CREATE INDEX idx_subscriptions_platform ON subscriptions(ai_platform_id, status);
CREATE INDEX idx_subscriptions_mcp ON subscriptions(mcp_id, status);
CREATE INDEX idx_subscriptions_active ON subscriptions(status) WHERE status = 'active';

-- Pricing tiers (tier lookup)
CREATE INDEX idx_pricing_tiers_mcp ON pricing_tiers(mcp_id, tier_order);

-- Daily stats (dashboard queries)
CREATE INDEX idx_daily_stats_date ON daily_stats(date DESC);
CREATE INDEX idx_daily_stats_mcp ON daily_stats(mcp_id, date DESC);
CREATE INDEX idx_daily_stats_platform ON daily_stats(ai_platform_id, date DESC);

-- Rate cards (pricing lookups)
CREATE INDEX idx_rate_cards_city ON rate_cards(city);
CREATE INDEX idx_rate_cards_lookup ON rate_cards(city, service, ride_type, is_active);

-- Surge history (ML queries)
CREATE INDEX idx_surge_city_time ON surge_history(city, recorded_at DESC);
CREATE INDEX idx_surge_prediction ON surge_history(city, day_of_week, hour_of_day);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update timestamp to relevant tables
CREATE TRIGGER update_developers_timestamp BEFORE UPDATE ON developers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mcps_timestamp BEFORE UPDATE ON mcps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_platforms_timestamp BEFORE UPDATE ON ai_platforms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payouts_timestamp BEFORE UPDATE ON payouts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoices_timestamp BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_circuit_breaker_timestamp BEFORE UPDATE ON circuit_breaker_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_timestamp BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pricing_tiers_timestamp BEFORE UPDATE ON pricing_tiers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update MCP stats after each transaction
CREATE OR REPLACE FUNCTION update_mcp_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        UPDATE mcps SET
            total_requests = total_requests + 1,
            avg_response_time_ms = (
                (avg_response_time_ms * total_requests + NEW.response_time_ms) / (total_requests + 1)
            )::INTEGER
        WHERE id = NEW.mcp_id;
    ELSIF NEW.status = 'failed' THEN
        UPDATE mcps SET
            total_requests = total_requests + 1,
            total_errors = total_errors + 1
        WHERE id = NEW.mcp_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_mcp_stats_trigger AFTER INSERT OR UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_mcp_stats();

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- MCP Directory (public-facing info)
CREATE VIEW mcp_directory AS
SELECT
    m.id,
    m.name,
    m.slug,
    m.description,
    m.category,
    m.version,
    m.connectivity_type,
    m.fee_per_request,
    m.avg_response_time_ms,
    m.avg_rating,
    m.uptime_percent,
    m.tags,
    m.supported_regions,
    d.display_name as developer_name,
    d.company_name as developer_company,
    (SELECT COUNT(*) FROM mcp_capabilities WHERE mcp_id = m.id) as capability_count
FROM mcps m
JOIN developers d ON m.developer_id = d.id
WHERE m.status = 'active';

-- Revenue Summary (for admin dashboard)
CREATE VIEW revenue_summary AS
SELECT
    date,
    SUM(gross_revenue) as total_gross,
    SUM(platform_revenue) as total_platform,
    SUM(developer_revenue) as total_developer,
    SUM(total_requests) as total_requests,
    SUM(failed_requests) as total_failed
FROM daily_stats
GROUP BY date
ORDER BY date DESC;

-- Developer Dashboard
CREATE VIEW developer_dashboard AS
SELECT
    d.id as developer_id,
    d.display_name,
    d.company_name,
    COUNT(DISTINCT m.id) as mcp_count,
    SUM(ds.total_requests) as total_requests,
    SUM(ds.developer_revenue) as total_revenue,
    AVG(m.avg_rating) as avg_rating
FROM developers d
LEFT JOIN mcps m ON d.id = m.developer_id
LEFT JOIN daily_stats ds ON m.id = ds.mcp_id
GROUP BY d.id, d.display_name, d.company_name;

-- ============================================
-- ROW LEVEL SECURITY (for multi-tenant safety)
-- ============================================

-- Enable RLS on sensitive tables
ALTER TABLE developers ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- Note: Policies would be created based on the authentication system
-- Example policy (commented out, implement based on your auth):
-- CREATE POLICY developer_isolation ON transactions
--     FOR ALL
--     USING (developer_id = current_setting('app.current_developer_id')::uuid);

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE mcps IS 'Registry of all Model Context Protocol servers in the marketplace';
COMMENT ON TABLE developers IS 'MCP developers/companies who build and maintain MCPs';
COMMENT ON TABLE ai_platforms IS 'AI platforms (Claude, ChatGPT) that consume MCPs through our API';
COMMENT ON TABLE transactions IS 'Every billable API request through the platform (supports multiple pricing models)';
COMMENT ON TABLE rate_cards IS 'Rideshare pricing data for the flagship comparison MCP';
COMMENT ON TABLE circuit_breaker_state IS 'Fault tolerance state for each MCP (closed/open/half-open)';
COMMENT ON TABLE subscriptions IS 'Active subscriptions for subscription/hybrid pricing models';
COMMENT ON TABLE pricing_tiers IS 'Volume-based pricing tiers for tiered pricing model';

-- MCP pricing comments
COMMENT ON COLUMN mcps.pricing_model IS 'Billing strategy: per_request (default), subscription, commission, tiered, hybrid';
COMMENT ON COLUMN mcps.developer_share IS 'Fraction of fee paid to developer (0.80 = 80%), configurable per-MCP';
COMMENT ON COLUMN mcps.fee_per_request IS 'Amount charged to AI platform per request (USD), used in per_request/hybrid models';
COMMENT ON COLUMN mcps.commission_rate IS 'Commission percentage for commission model (e.g., 0.10 = 10%)';
COMMENT ON COLUMN mcps.subscription_fee IS 'Monthly fee for subscription/hybrid models';
COMMENT ON COLUMN mcps.connectivity_type IS 'How to connect: http (REST), email (SMTP), oauth, webhook (inbound), graphql, async (long-running)';
COMMENT ON COLUMN mcps.email_address IS 'Email address for email-based MCPs';
COMMENT ON COLUMN mcps.webhook_path IS 'Our endpoint path for webhook-based MCPs (they call us)';

-- Transaction billing comments
COMMENT ON COLUMN transactions.gross_amount IS 'Total charged to AI platform (calculated based on pricing_model)';
COMMENT ON COLUMN transactions.platform_fee IS 'Our cut (configurable per-MCP via developer_share)';
COMMENT ON COLUMN transactions.developer_payout IS 'Developer cut (configurable per-MCP via developer_share)';
COMMENT ON COLUMN transactions.pricing_model IS 'How this transaction was billed: per_request, subscription, commission, tiered, hybrid';
COMMENT ON COLUMN transactions.subscription_id IS 'Reference to active subscription (subscription/hybrid models)';
COMMENT ON COLUMN transactions.booking_value IS 'Original transaction value for commission model (e.g., ride fare)';
COMMENT ON COLUMN transactions.commission_rate IS 'Commission rate applied for commission model';
COMMENT ON COLUMN transactions.tier_name IS 'Tier applied for tiered pricing (e.g., starter, enterprise)';
