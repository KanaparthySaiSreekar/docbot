-- Payment tracking for reconciliation
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    appointment_id TEXT NOT NULL REFERENCES appointments(id),
    razorpay_payment_link_id TEXT,
    razorpay_payment_id TEXT,
    amount_paise INTEGER NOT NULL,  -- 50000 for ₹500
    status TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING, CAPTURED, FAILED
    created_at TEXT NOT NULL,
    captured_at TEXT,
    UNIQUE(appointment_id)
);

CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_link_id ON payments(razorpay_payment_link_id);
