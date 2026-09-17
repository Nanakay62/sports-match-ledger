-- ============================================================================
-- Sports News AI — Least-Privilege Database Roles Initialization
-- Enforces Append-Only Invariants at the PostgreSQL Privilege Layer (§11 & §19)
-- ============================================================================

-- Ensure the public schema exists
CREATE SCHEMA IF NOT EXISTS public;

-- ----------------------------------------------------------------------------
-- 1. Read-Write Application Role (app_rw)
-- Used by the FastAPI backend and ingestion workers.
-- Explicitly DENIES UPDATE and DELETE on immutable ledger tables.
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_rw') THEN
        CREATE ROLE app_rw WITH LOGIN PASSWORD 'app_rw_secure_change_me_in_prod';
    END IF;
END
$$;

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO app_rw;

-- Grant SELECT and INSERT on all core ledger tables
GRANT SELECT, INSERT ON TABLE claims TO app_rw;
GRANT SELECT, INSERT ON TABLE claim_evidence TO app_rw;
GRANT SELECT, INSERT ON TABLE resolutions TO app_rw;

-- Explicitly DO NOT grant UPDATE or DELETE on claims or resolutions
-- Any attempt to modify or delete a recorded claim will be rejected by both
-- database role permissions and table triggers (init_immutability_triggers.sql).

-- Grant SELECT, INSERT, UPDATE, DELETE on mutable operational tables
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE events TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE sources TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reporters TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE source_registry TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE pipeline_jobs TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE dead_letter_jobs TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE quarantined_documents TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE editorial_evaluation_logs TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE event_translations TO app_rw;

-- Grant sequence permissions for autoincrementing IDs
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_rw;

-- ----------------------------------------------------------------------------
-- 2. Read-Only Reporting Role (app_ro)
-- Used for public read replicas, external analytics, and cache warmup.
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_ro') THEN
        CREATE ROLE app_ro WITH LOGIN PASSWORD 'app_ro_secure_change_me_in_prod';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO app_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_ro;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO app_ro;

-- Restrict schema creation to superusers
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
