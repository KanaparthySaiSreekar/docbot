-- Patients and conversations schema for WhatsApp bot state management
-- Supports language persistence and booking flow tracking

-- Patients table for language preference persistence (BOT-03)
CREATE TABLE IF NOT EXISTS patients (
    phone TEXT PRIMARY KEY,           -- E.164 format e.g. "919876543210"
    language TEXT NOT NULL DEFAULT 'en',  -- 'en', 'te', 'hi'
    name TEXT,                        -- Populated during booking
    created_at TEXT NOT NULL,         -- UTC ISO 8601
    updated_at TEXT NOT NULL          -- UTC ISO 8601
);

-- Conversations table for tracking booking flow state (BOT-09)
CREATE TABLE IF NOT EXISTS conversations (
    phone TEXT PRIMARY KEY,           -- One active conversation per phone (BOT-09)
    state TEXT NOT NULL,              -- Current step in flow
    data TEXT,                        -- JSON blob for accumulated booking data
    started_at TEXT NOT NULL,         -- UTC ISO 8601
    updated_at TEXT NOT NULL,         -- UTC ISO 8601
    expires_at TEXT NOT NULL          -- UTC ISO 8601 - conversation timeout
);

CREATE INDEX IF NOT EXISTS idx_conversations_expires ON conversations(expires_at);
