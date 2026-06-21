-- Run this in the Supabase SQL Editor (once, after 01_schema.sql)
-- Needed because the REST API can't do random + NOT IN subquery in one call.

CREATE OR REPLACE FUNCTION get_next_question(p_user_id BIGINT)
RETURNS TABLE(
    id            BIGINT,
    topic         TEXT,
    question      TEXT,
    option_a      TEXT,
    option_b      TEXT,
    option_c      TEXT,
    option_d      TEXT,
    correct_answer CHAR(1)
)
LANGUAGE SQL SECURITY DEFINER AS $$
    SELECT id, topic, question, option_a, option_b, option_c, option_d, correct_answer
    FROM questions
    WHERE id NOT IN (
        SELECT question_id FROM answers_log WHERE user_id = p_user_id
    )
    ORDER BY RANDOM()
    LIMIT 1;
$$;
