-- Ensure prescriptions table has all required columns
-- Already exists from 001_initial_schema.sql, but add secure_token for URL access
ALTER TABLE prescriptions ADD COLUMN secure_token TEXT;
ALTER TABLE prescriptions ADD COLUMN token_expires_at TEXT;
ALTER TABLE prescriptions ADD COLUMN whatsapp_sent TEXT DEFAULT 'false';

CREATE INDEX IF NOT EXISTS idx_prescriptions_token ON prescriptions(secure_token);
CREATE INDEX IF NOT EXISTS idx_prescriptions_appointment ON prescriptions(appointment_id);
