BEGIN;

CREATE TABLE IF NOT EXISTS public.support_app_logs (
    id BIGSERIAL PRIMARY KEY,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    request_id TEXT,
    user_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.support_function_runs (
    id BIGSERIAL PRIMARY KEY,
    function_name TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INTEGER NOT NULL,
    error_class TEXT,
    version TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.support_auth_events (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    provider TEXT,
    status TEXT NOT NULL,
    detail TEXT,
    occurred_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.support_access_events (
    id BIGSERIAL PRIMARY KEY,
    actor_id TEXT NOT NULL,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    allowed BOOLEAN NOT NULL,
    denial_reason TEXT,
    occurred_at TIMESTAMPTZ NOT NULL
);

INSERT INTO public.support_app_logs (level, message, request_id, user_id, created_at) VALUES
('ERROR', 'permission denied while accessing tenant profile', 'req-1001', 'user-01', NOW() - INTERVAL '20 minutes'),
('ERROR', 'timeout querying account service', 'req-1002', 'user-02', NOW() - INTERVAL '18 minutes'),
('WARN', 'retry burst detected for payment webhook', 'req-1003', 'user-07', NOW() - INTERVAL '15 minutes'),
('INFO', 'healthcheck ok', 'req-1004', NULL, NOW() - INTERVAL '10 minutes')
ON CONFLICT DO NOTHING;

INSERT INTO public.support_function_runs (function_name, status, latency_ms, error_class, version, started_at) VALUES
('sync_customer_profile', 'failed', 1250, 'permission_denied', 'v1.2.7', NOW() - INTERVAL '21 minutes'),
('sync_customer_profile', 'failed', 1410, 'timeout', 'v1.2.7', NOW() - INTERVAL '19 minutes'),
('billing_rollup', 'succeeded', 210, NULL, 'v2.1.0', NOW() - INTERVAL '8 minutes')
ON CONFLICT DO NOTHING;

INSERT INTO public.support_auth_events (user_id, event_type, provider, status, detail, occurred_at) VALUES
('user-01', 'sign_in', 'google', 'failed', 'invalid_grant', NOW() - INTERVAL '40 minutes'),
('user-01', 'token_refresh', 'google', 'failed', 'expired_refresh_token', NOW() - INTERVAL '39 minutes'),
('user-02', 'sign_in', 'github', 'success', NULL, NOW() - INTERVAL '30 minutes')
ON CONFLICT DO NOTHING;

INSERT INTO public.support_access_events (actor_id, resource, action, allowed, denial_reason, occurred_at) VALUES
('user-01', 'tenant_profiles', 'select', false, 'rls_policy_tenant_scope', NOW() - INTERVAL '20 minutes'),
('user-02', 'tenant_profiles', 'select', true, NULL, NOW() - INTERVAL '16 minutes'),
('user-03', 'billing_invoices', 'select', false, 'missing_role_support_billing_read', NOW() - INTERVAL '14 minutes')
ON CONFLICT DO NOTHING;

COMMIT;
