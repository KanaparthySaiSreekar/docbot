-- Refund tracking for retry mechanism
CREATE TABLE IF NOT EXISTS refunds (
    id TEXT PRIMARY KEY,
    appointment_id TEXT NOT NULL REFERENCES appointments(id),
    razorpay_payment_id TEXT NOT NULL,
    razorpay_refund_id TEXT,
    amount_paise INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING, PROCESSING, PROCESSED, FAILED
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at TEXT,  -- UTC timestamp for exponential backoff
    created_at TEXT NOT NULL,
    processed_at TEXT,
    UNIQUE(appointment_id)
);

CREATE INDEX IF NOT EXISTS idx_refunds_status ON refunds(status);
CREATE INDEX IF NOT EXISTS idx_refunds_next_retry ON refunds(next_retry_at);
