-- Initial schema for DocBot appointment system
-- UTC timestamps, database-level locking, aggressive indexing

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Use WAL mode for better concurrent read performance
PRAGMA journal_mode = WAL;

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,  -- UUID
    patient_phone TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    patient_age INTEGER NOT NULL,
    patient_gender TEXT NOT NULL CHECK (patient_gender IN ('Male', 'Female', 'Other')),
    consultation_type TEXT NOT NULL CHECK (consultation_type IN ('online', 'offline')),
    appointment_date TEXT NOT NULL,  -- ISO date YYYY-MM-DD
    slot_time TEXT NOT NULL,  -- HH:MM format
    status TEXT NOT NULL DEFAULT 'PENDING_PAYMENT',
    razorpay_payment_id TEXT,
    razorpay_order_id TEXT,
    razorpay_refund_id TEXT,
    google_calendar_event_id TEXT,
    google_meet_link TEXT,
    language TEXT NOT NULL DEFAULT 'en',
    created_at TEXT NOT NULL,  -- ISO 8601 UTC
    updated_at TEXT NOT NULL,  -- ISO 8601 UTC
    cancelled_at TEXT,
    refunded_at TEXT
);

-- Slot locks table (database-level locking)
-- PRIMARY KEY constraint enforces slot uniqueness
CREATE TABLE IF NOT EXISTS slot_locks (
    appointment_date TEXT NOT NULL,
    slot_time TEXT NOT NULL,
    locked_by_phone TEXT NOT NULL,
    locked_until TEXT NOT NULL,  -- UTC timestamp
    PRIMARY KEY (appointment_date, slot_time)
);

-- Idempotency keys table for webhook deduplication
CREATE TABLE IF NOT EXISTS idempotency_keys (
    event_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,  -- 'razorpay', 'whatsapp', etc.
    processed_at TEXT NOT NULL,  -- UTC timestamp
    result TEXT  -- JSON string of processing result
);

-- Prescriptions table
CREATE TABLE IF NOT EXISTS prescriptions (
    id TEXT PRIMARY KEY,  -- UUID
    appointment_id TEXT NOT NULL REFERENCES appointments(id),
    medicines TEXT NOT NULL,  -- JSON
    instructions TEXT,
    pdf_path TEXT,
    created_at TEXT NOT NULL,  -- UTC timestamp
    UNIQUE(appointment_id)  -- One prescription per appointment
);

-- Indexes for query optimization

-- Appointments indexes
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_phone ON appointments(patient_phone);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_date_status ON appointments(appointment_date, status);
CREATE INDEX IF NOT EXISTS idx_appointments_date_slot ON appointments(appointment_date, slot_time);

-- Slot locks indexes
CREATE INDEX IF NOT EXISTS idx_slot_locks_until ON slot_locks(locked_until);

-- Idempotency indexes
CREATE INDEX IF NOT EXISTS idx_idempotency_source ON idempotency_keys(source);
