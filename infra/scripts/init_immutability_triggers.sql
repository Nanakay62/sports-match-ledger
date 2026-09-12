-- PostgreSQL Immutability Triggers for Sports News AI Ledger
-- Enforces Phase 5 requirement: DB-level immutability rejecting UPDATE or DELETE on ledger claims

CREATE OR REPLACE FUNCTION prevent_claim_mutation()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        RAISE EXCEPTION 'Immutability violation: DELETE is forbidden on claims table. Claims may only be superseded.';
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Allow updating only the supersession pointer flags, never claim_text, source_id, or original_url
        IF (OLD.claim_text <> NEW.claim_text OR OLD.source_id <> NEW.source_id OR OLD.original_url <> NEW.original_url) THEN
            RAISE EXCEPTION 'Immutability violation: UPDATE on claim content is forbidden. Record a new superseding claim instead.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_enforce_claim_immutability
BEFORE UPDATE OR DELETE ON claims
FOR EACH ROW
EXECUTE FUNCTION prevent_claim_mutation();

-- Enforce immutability on resolutions
CREATE OR REPLACE FUNCTION prevent_resolution_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutability violation: Resolutions table is append-only. UPDATE and DELETE are prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_enforce_resolution_immutability
BEFORE UPDATE OR DELETE ON resolutions
FOR EACH ROW
EXECUTE FUNCTION prevent_resolution_mutation();
