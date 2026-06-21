-- ============================================================
-- Telegram Quiz Bot — Supabase Schema
-- Run this first, before any data import
-- ============================================================

-- ── questions ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS questions (
    id              BIGSERIAL PRIMARY KEY,
    topic           TEXT        NOT NULL,
    question        TEXT        NOT NULL,
    option_a        TEXT        NOT NULL,   -- displayed as "1."
    option_b        TEXT        NOT NULL,   -- displayed as "2."
    option_c        TEXT        NOT NULL,   -- displayed as "3."
    option_d        TEXT        NOT NULL,   -- displayed as "4."
    correct_answer  CHAR(1)     NOT NULL CHECK (correct_answer IN ('1','2','3','4')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions (topic);

-- ── users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id               BIGSERIAL   PRIMARY KEY,
    telegram_user_id BIGINT      NOT NULL UNIQUE,
    name             TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users (telegram_user_id);

-- ── answers_log ──────────────────────────────────────────────
-- Tracks every answered question per user. Used to avoid repeats:
-- next question is drawn from questions NOT IN this table for the user.
CREATE TABLE IF NOT EXISTS answers_log (
    id           BIGSERIAL   PRIMARY KEY,
    user_id      BIGINT      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    question_id  BIGINT      NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    was_correct  BOOLEAN     NOT NULL,
    answered_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_answers_log_user_id     ON answers_log (user_id);
CREATE INDEX IF NOT EXISTS idx_answers_log_question_id ON answers_log (question_id);

-- ── question_flags ───────────────────────────────────────────
-- Populated when a user taps "סמן כשאלה לא ברורה".
-- Use to review and fix questions that users find confusing.
CREATE TABLE IF NOT EXISTS question_flags (
    id           BIGSERIAL   PRIMARY KEY,
    user_id      BIGINT      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    question_id  BIGINT      NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    flagged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, question_id)   -- one flag per user per question
);

CREATE INDEX IF NOT EXISTS idx_question_flags_question_id ON question_flags (question_id);

-- ── Convenience view: questions ranked by unclear flag count ─
-- Use in Supabase dashboard to see which questions need review.
CREATE OR REPLACE VIEW unclear_questions AS
SELECT
    q.id,
    q.topic,
    q.question,
    q.correct_answer,
    COUNT(f.id) AS flag_count
FROM questions q
JOIN question_flags f ON f.question_id = q.id
GROUP BY q.id, q.topic, q.question, q.correct_answer
ORDER BY flag_count DESC;
