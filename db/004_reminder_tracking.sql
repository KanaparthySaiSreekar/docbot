-- Add reminder tracking columns to appointments
-- Tracks whether 24-hour and 1-hour reminders have been sent

-- Add reminder tracking columns
ALTER TABLE appointments ADD COLUMN reminder_sent_24h TEXT DEFAULT 'false';
ALTER TABLE appointments ADD COLUMN reminder_sent_1h TEXT DEFAULT 'false';

-- Index for efficient reminder queries
-- Allows fast lookups of appointments needing reminders
CREATE INDEX IF NOT EXISTS idx_appointments_reminder_24h ON appointments(reminder_sent_24h, appointment_date, status);
CREATE INDEX IF NOT EXISTS idx_appointments_reminder_1h ON appointments(reminder_sent_1h, appointment_date, status);
