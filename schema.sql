-- =========================
-- USERS
-- =========================
CREATE TABLE IF NOT EXISTS users (
    user_id     BIGINT PRIMARY KEY,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- =========================
-- BALANCES
-- =========================
CREATE TABLE IF NOT EXISTS balances (
    user_id     BIGINT PRIMARY KEY
        REFERENCES users(user_id) ON DELETE CASCADE,
    balance     INTEGER NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- =========================
-- FREE TRIES (1 marta tekin)
-- =========================
CREATE TABLE IF NOT EXISTS free_tries (
    user_id     BIGINT PRIMARY KEY
        REFERENCES users(user_id) ON DELETE CASCADE,
    used_at     TIMESTAMPTZ DEFAULT now()
);

-- =========================
-- ENUMS
-- =========================
DO $$
BEGIN
    -- receipt_kind
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'receipt_kind') THEN
        CREATE TYPE receipt_kind AS ENUM ('photo', 'document');
    END IF;

    -- payment_status
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status') THEN
        CREATE TYPE payment_status AS ENUM ('pending', 'approved', 'rejected');
    END IF;
END $$;

-- =========================
-- PAYMENTS
-- =========================
CREATE TABLE IF NOT EXISTS payments (
    payment_id        TEXT PRIMARY KEY,
    user_id           BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE CASCADE,
    amount            INTEGER NOT NULL DEFAULT 1,
    status            payment_status NOT NULL DEFAULT 'pending',
    username          TEXT,
    receipt_kind      receipt_kind NOT NULL,
    receipt_file_id   TEXT NOT NULL,

    created_at        TIMESTAMPTZ DEFAULT now(),
    decided_at        TIMESTAMPTZ,
    decided_by        BIGINT
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- =========================
-- ESSAY REVIEWS (Admin voice workflow)
-- =========================

-- Create enum if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'essay_review_status') THEN
        CREATE TYPE essay_review_status AS ENUM (
            'waiting_voice',
            'voice_scheduled',
            'voice_sent',
            'resent',
            'completed'
        );
    END IF;
END $$;

-- Add missing enum values safely (if enum already exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'essay_review_status') THEN

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'essay_review_status' AND e.enumlabel = 'waiting_voice'
        ) THEN
            ALTER TYPE essay_review_status ADD VALUE 'waiting_voice';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'essay_review_status' AND e.enumlabel = 'voice_scheduled'
        ) THEN
            ALTER TYPE essay_review_status ADD VALUE 'voice_scheduled';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'essay_review_status' AND e.enumlabel = 'voice_sent'
        ) THEN
            ALTER TYPE essay_review_status ADD VALUE 'voice_sent';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'essay_review_status' AND e.enumlabel = 'resent'
        ) THEN
            ALTER TYPE essay_review_status ADD VALUE 'resent';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'essay_review_status' AND e.enumlabel = 'completed'
        ) THEN
            ALTER TYPE essay_review_status ADD VALUE 'completed';
        END IF;

    END IF;
END $$;

-- Main table
CREATE TABLE IF NOT EXISTS essay_reviews (
    essay_id        TEXT PRIMARY KEY,

    user_id         BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE CASCADE,

    topic           TEXT NOT NULL,
    essay_text      TEXT NOT NULL,
    ai_result       TEXT NOT NULL,

    -- Admin message that contains the AI result (so admin must reply to it)
    admin_chat_id   BIGINT NOT NULL,
    admin_msg_id    BIGINT NOT NULL,

    -- Voice that admin records (Telegram file_id)
    voice_file_id   TEXT,

    status          essay_review_status NOT NULL DEFAULT 'waiting_voice',

    created_at      TIMESTAMPTZ DEFAULT now(),

    -- When admin recorded/accepted voice (audit)
    voiced_at       TIMESTAMPTZ,

    -- When voice was sent to user (audit)
    sent_to_user_at TIMESTAMPTZ,

    -- Extra audit fields used by your code
    voice_sent_at   TIMESTAMPTZ,
    voice_sent_by   BIGINT,
    voice_msg_id    BIGINT
);

CREATE INDEX IF NOT EXISTS idx_essay_reviews_user_id ON essay_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_essay_reviews_status ON essay_reviews(status);
CREATE INDEX IF NOT EXISTS idx_essay_reviews_admin_msg ON essay_reviews(admin_chat_id, admin_msg_id);
