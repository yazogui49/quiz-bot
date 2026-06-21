import os
from typing import Optional
import asyncpg

_pool: Optional[asyncpg.Pool] = None


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=1,
        max_size=5,
        statement_cache_size=0,
    )


async def close_pool() -> None:
    if _pool:
        await _pool.close()


def _pool_or_raise() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised")
    return _pool


async def upsert_user(telegram_user_id: int, name: str) -> int:
    row = await _pool_or_raise().fetchrow(
        """
        INSERT INTO users (telegram_user_id, name)
        VALUES ($1, $2)
        ON CONFLICT (telegram_user_id) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        telegram_user_id,
        name,
    )
    return row["id"]


async def get_next_question(user_id: int) -> Optional[dict]:
    row = await _pool_or_raise().fetchrow(
        """
        SELECT id, question, option_a, option_b, option_c, option_d, correct_answer
        FROM questions
        WHERE id NOT IN (
            SELECT question_id FROM answers_log WHERE user_id = $1
        )
        ORDER BY RANDOM()
        LIMIT 1
        """,
        user_id,
    )
    return dict(row) if row else None


async def get_question_by_id(question_id: int) -> Optional[dict]:
    row = await _pool_or_raise().fetchrow(
        "SELECT id, option_a, option_b, option_c, option_d, correct_answer FROM questions WHERE id = $1",
        question_id,
    )
    return dict(row) if row else None


async def log_answer(user_id: int, question_id: int, was_correct: bool) -> None:
    await _pool_or_raise().execute(
        "INSERT INTO answers_log (user_id, question_id, was_correct) VALUES ($1, $2, $3)",
        user_id,
        question_id,
        was_correct,
    )


async def flag_question(user_id: int, question_id: int) -> None:
    await _pool_or_raise().execute(
        """
        INSERT INTO question_flags (user_id, question_id)
        VALUES ($1, $2)
        ON CONFLICT (user_id, question_id) DO NOTHING
        """,
        user_id,
        question_id,
    )


async def clear_history(user_id: int) -> None:
    await _pool_or_raise().execute(
        "DELETE FROM answers_log WHERE user_id = $1",
        user_id,
    )
