-- MCP Aggregator Platform - Seed Data
-- Version: 1.0.0
-- Created: 2026-01-12
--
-- Initial data for development and testing:
-- - Default developer (William/internal)
-- - Rideshare Comparison MCP (flagship)
-- - Sample AI platform (for testing)
-- - Rate cards for 10 major cities

-- ============================================
-- DEVELOPERS
-- ============================================

-- Internal developer (William/platform owner)
INSERT INTO developers (id, email, company_name, display_name, api_key_hash, is_verified, is_active)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'william@mcp-aggregator.com',
    'MCP Aggregator Inc.',
    'William Marceau Jr.',
    -- API key: 'dev_internal_key_12345' (bcrypt hash)
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.UMfzxZU3lT8Gq.',
    TRUE,
    TRUE
);

-- Sample third-party developer
INSERT INTO developers (id, email, company_name, display_name, api_key_hash, is_verified, is_active)
VALUES (
    'a0000000-0000-0000-0000-000000000002',
    'demo@example.com',
    'Demo MCP Builders',
    'Demo Developer',
    -- API key: 'dev_demo_key_67890' (bcrypt hash)
    '$2b$12$RQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.UMfzxZU3lT8Abc',
    TRUE,
    TRUE
);

-- ============================================
-- AI PLATFORMS
-- ============================================

-- Claude (Anthropic) - Primary integration
INSERT INTO ai_platforms (id, name, api_key_hash, contact_email, billing_email, monthly_credit_limit, is_active)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'Claude (Anthropic)',
    -- API key: 'claude_platform_key_abc123' (bcrypt hash)
    '$2b$12$XQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.UMfzxZU3lT8Xyz',
    'mcp-support@anthropic.com',
    'billing@anthropic.com',
    100000.00,
    TRUE
);

-- Development/Testing Platform
INSERT INTO ai_platforms (id, name, api_key_hash, contact_email, billing_email, monthly_credit_limit, is_active)
VALUES (
    'b0000000-0000-0000-0000-000000000002',
    'Development Testing',
    -- API key: 'test_platform_key_dev' (bcrypt hash)
    '$2b$12$YQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.UMfzxZU3lT8Dev',
    'dev@mcp-aggregator.com',
    'dev@mcp-aggregator.com',
    1000.00,
    TRUE
);

-- ============================================
-- MCPS (Model Context Protocol Servers)
-- ============================================

-- Rideshare Comparison MCP (FLAGSHIP)
INSERT INTO mcps (
    id, developer_id, name, slug, description, category, version,
    endpoint_url, health_check_url, documentation_url,
    fee_per_request, developer_share, status,
    avg_response_time_ms, avg_rating, uptime_percent,
    tags, supported_regions, rate_limit_rpm, timeout_ms
)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Rideshare Price Comparison',
    'rideshare-comparison',
    'Compare Uber and Lyft prices in real-time. Uses proprietary algorithm based on public rate cards for 85%+ accuracy. Returns price estimates, surge factors, and deep links to book.',
    'rideshare',
    '1.0.0',
    'http://localhost:8000/v1/mcps/rideshare/compare',
    'http://localhost:8000/v1/mcps/rideshare/health',
    'https://docs.mcp-aggregator.com/mcps/rideshare',
    0.02,  -- $0.02 per comparison
    0.80,  -- 80% to developer (us, in this case)
    'active',
    150,  -- ~150ms response time
    4.80,
    99.95,
    ARRAY['rideshare', 'uber', 'lyft', 'pricing', 'realtime', 'geolocation'],
    ARRAY['us'],
    1000,  -- 1000 RPM
    5000   -- 5 second timeout
);

-- Sample Weather MCP (third-party example)
INSERT INTO mcps (
    id, developer_id, name, slug, description, category, version,
    endpoint_url, health_check_url,
    fee_per_request, developer_share, status,
    tags, supported_regions, rate_limit_rpm, timeout_ms
)
VALUES (
    'c0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000002',
    'Weather Lookup',
    'weather-lookup',
    'Get current weather and 7-day forecast for any location. Supports coordinates or city names.',
    'utilities',
    '1.0.0',
    'http://example.com/v1/weather',
    'http://example.com/v1/weather/health',
    0.005,  -- $0.005 per lookup
    0.80,
    'active',
    ARRAY['weather', 'forecast', 'geolocation'],
    ARRAY['global'],
    500,
    3000
);

-- ============================================
-- MCP CAPABILITIES
-- ============================================

-- Rideshare MCP Capabilities
INSERT INTO mcp_capabilities (mcp_id, name, description, input_schema, output_schema, examples)
VALUES
(
    'c0000000-0000-0000-0000-000000000001',
    'compare_prices',
    'Compare Uber and Lyft prices for a given route',
    '{
        "type": "object",
        "required": ["pickup", "dropoff"],
        "properties": {
            "pickup": {
                "type": "object",
                "required": ["latitude", "longitude"],
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "address": {"type": "string"}
                }
            },
            "dropoff": {
                "type": "object",
                "required": ["latitude", "longitude"],
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "address": {"type": "string"}
                }
            },
            "city": {"type": "string"}
        }
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "uber": {"$ref": "#/definitions/FareEstimate"},
            "lyft": {"$ref": "#/definitions/FareEstimate"},
            "recommendation": {"type": "string", "enum": ["uber", "lyft"]},
            "savings": {"type": "number"}
        },
        "definitions": {
            "FareEstimate": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "ride_type": {"type": "string"},
                    "estimate": {"type": "number"},
                    "low_estimate": {"type": "number"},
                    "high_estimate": {"type": "number"},
                    "surge_multiplier": {"type": "number"},
                    "distance_miles": {"type": "number"},
                    "duration_minutes": {"type": "number"},
                    "deep_link": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        }
    }'::jsonb,
    '[
        {
            "description": "Union Square SF to SFO Airport",
            "input": {
                "pickup": {"latitude": 37.7879, "longitude": -122.4074},
                "dropoff": {"latitude": 37.6213, "longitude": -122.3790}
            },
            "output": {
                "uber": {"estimate": 42.50, "deep_link": "uber://..."},
                "lyft": {"estimate": 38.25, "deep_link": "lyft://..."},
                "recommendation": "lyft",
                "savings": 4.25
            }
        }
    ]'::jsonb
),
(
    'c0000000-0000-0000-0000-000000000001',
    'get_supported_cities',
    'Get list of cities where price comparison is available',
    '{"type": "object", "properties": {}}'::jsonb,
    '{
        "type": "object",
        "properties": {
            "cities": {
                "type": "array",
                "items": {"type": "string"}
            },
            "count": {"type": "integer"}
        }
    }'::jsonb,
    '[
        {
            "description": "Get all supported cities",
            "input": {},
            "output": {
                "cities": ["san_francisco", "new_york", "los_angeles"],
                "count": 10
            }
        }
    ]'::jsonb
);

-- Weather MCP Capabilities
INSERT INTO mcp_capabilities (mcp_id, name, description, input_schema, output_schema)
VALUES
(
    'c0000000-0000-0000-0000-000000000002',
    'current_weather',
    'Get current weather conditions',
    '{
        "type": "object",
        "required": ["location"],
        "properties": {
            "location": {"type": "string"},
            "units": {"type": "string", "enum": ["metric", "imperial"], "default": "imperial"}
        }
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "temperature": {"type": "number"},
            "feels_like": {"type": "number"},
            "humidity": {"type": "number"},
            "conditions": {"type": "string"},
            "wind_speed": {"type": "number"}
        }
    }'::jsonb
);

-- ============================================
-- CIRCUIT BREAKER STATE (all start closed)
-- ============================================

INSERT INTO circuit_breaker_state (mcp_id, state, failure_count, success_count)
VALUES
    ('c0000000-0000-0000-0000-000000000001', 'closed', 0, 0),
    ('c0000000-0000-0000-0000-000000000002', 'closed', 0, 0);

-- ============================================
-- RATE CARDS (Rideshare Pricing Data)
-- ============================================

-- San Francisco
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('san_francisco', 'uber', 'uberx', 2.55, 1.75, 0.30, 2.70, 7.65, '2026-01-01', TRUE),
    ('san_francisco', 'uber', 'uber_xl', 4.50, 2.85, 0.50, 3.00, 10.00, '2026-01-01', TRUE),
    ('san_francisco', 'lyft', 'lyft', 2.00, 1.50, 0.35, 2.70, 6.00, '2026-01-01', TRUE),
    ('san_francisco', 'lyft', 'lyft_xl', 3.75, 2.50, 0.55, 3.00, 9.00, '2026-01-01', TRUE);

-- New York
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('new_york', 'uber', 'uberx', 2.55, 1.95, 0.35, 2.75, 8.00, '2026-01-01', TRUE),
    ('new_york', 'lyft', 'lyft', 2.00, 1.71, 0.42, 2.75, 7.00, '2026-01-01', TRUE);

-- Los Angeles
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('los_angeles', 'uber', 'uberx', 2.20, 1.20, 0.21, 2.40, 5.50, '2026-01-01', TRUE),
    ('los_angeles', 'lyft', 'lyft', 1.82, 1.08, 0.27, 2.40, 5.00, '2026-01-01', TRUE);

-- Chicago
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('chicago', 'uber', 'uberx', 2.20, 1.45, 0.25, 2.40, 6.55, '2026-01-01', TRUE),
    ('chicago', 'lyft', 'lyft', 1.70, 1.20, 0.30, 2.40, 5.75, '2026-01-01', TRUE);

-- Boston
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('boston', 'uber', 'uberx', 2.55, 1.65, 0.35, 2.55, 7.25, '2026-01-01', TRUE),
    ('boston', 'lyft', 'lyft', 2.00, 1.42, 0.39, 2.55, 6.50, '2026-01-01', TRUE);

-- Seattle
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('seattle', 'uber', 'uberx', 2.45, 1.55, 0.28, 2.65, 6.95, '2026-01-01', TRUE),
    ('seattle', 'lyft', 'lyft', 2.07, 1.33, 0.33, 2.65, 6.25, '2026-01-01', TRUE);

-- Austin
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('austin', 'uber', 'uberx', 2.00, 1.10, 0.19, 2.30, 5.30, '2026-01-01', TRUE),
    ('austin', 'lyft', 'lyft', 1.50, 0.95, 0.24, 2.30, 4.75, '2026-01-01', TRUE);

-- Miami
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('miami', 'uber', 'uberx', 2.15, 1.25, 0.22, 2.45, 5.80, '2026-01-01', TRUE),
    ('miami', 'lyft', 'lyft', 1.90, 1.10, 0.26, 2.45, 5.25, '2026-01-01', TRUE);

-- Denver
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('denver', 'uber', 'uberx', 2.25, 1.35, 0.23, 2.50, 6.00, '2026-01-01', TRUE),
    ('denver', 'lyft', 'lyft', 1.85, 1.18, 0.28, 2.50, 5.40, '2026-01-01', TRUE);

-- Washington DC
INSERT INTO rate_cards (city, service, ride_type, base_fare, cost_per_mile, cost_per_minute, booking_fee, min_fare, effective_date, is_active)
VALUES
    ('washington_dc', 'uber', 'uberx', 2.40, 1.60, 0.30, 2.60, 7.00, '2026-01-01', TRUE),
    ('washington_dc', 'lyft', 'lyft', 2.00, 1.38, 0.35, 2.60, 6.30, '2026-01-01', TRUE);

-- ============================================
-- SAMPLE TRANSACTIONS (for testing dashboards)
-- ============================================

-- Sample completed transaction
INSERT INTO transactions (
    id, ai_platform_id, mcp_id, developer_id,
    request_id, capability_name,
    request_payload, response_payload,
    started_at, completed_at, response_time_ms,
    gross_amount, platform_fee, developer_payout,
    status
)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000002',
    'c0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'req_sample_001',
    'compare_prices',
    '{"pickup": {"latitude": 37.7879, "longitude": -122.4074}, "dropoff": {"latitude": 37.6213, "longitude": -122.3790}}'::jsonb,
    '{"uber": {"estimate": 42.50}, "lyft": {"estimate": 38.25}, "recommendation": "lyft"}'::jsonb,
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '1 hour' + INTERVAL '145 milliseconds',
    145,
    0.02,
    0.004,
    0.016,
    'completed'
);

-- ============================================
-- SAMPLE DAILY STATS
-- ============================================

INSERT INTO daily_stats (
    date, mcp_id, ai_platform_id, developer_id,
    total_requests, successful_requests, failed_requests,
    avg_response_time_ms, p95_response_time_ms, p99_response_time_ms,
    gross_revenue, platform_revenue, developer_revenue
)
VALUES
    (CURRENT_DATE - INTERVAL '1 day', 'c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001',
     1250, 1238, 12, 142, 285, 450, 25.00, 5.00, 20.00),
    (CURRENT_DATE, 'c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001',
     500, 498, 2, 138, 265, 380, 10.00, 2.00, 8.00);

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Uncomment to verify data after seeding:
-- SELECT 'Developers:' as table_name, COUNT(*) as count FROM developers;
-- SELECT 'AI Platforms:' as table_name, COUNT(*) as count FROM ai_platforms;
-- SELECT 'MCPs:' as table_name, COUNT(*) as count FROM mcps;
-- SELECT 'Capabilities:' as table_name, COUNT(*) as count FROM mcp_capabilities;
-- SELECT 'Rate Cards:' as table_name, COUNT(*) as count FROM rate_cards;
-- SELECT 'Transactions:' as table_name, COUNT(*) as count FROM transactions;
