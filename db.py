import os
from typing import Optional
from supabase import create_client, Client

_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _client


async def upsert_user(telegram_user_id: int, name: str) -> int:
    result = (
        _get_client()
        .table("users")
        .upsert({"telegram_user_id": telegram_user_id, "name": name}, on_conflict="telegram_user_id")
        .execute()
    )
    return result.data[0]["id"]


async def get_next_question(user_id: int) -> Optional[dict]:
    result = _get_client().rpc("get_next_question", {"p_user_id": user_id}).execute()
    return result.data[0] if result.data else None


async def get_question_by_id(question_id: int) -> Optional[dict]:
    result = (
        _get_client()
        .table("questions")
        .select("id, option_a, option_b, option_c, option_d, correct_answer")
        .eq("id", question_id)
        .single()
        .execute()
    )
    return result.data


async def log_answer(user_id: int, question_id: int, was_correct: bool) -> None:
    _get_client().table("answers_log").insert(
        {"user_id": user_id, "question_id": question_id, "was_correct": was_correct}
    ).execute()


async def flag_question(user_id: int, question_id: int) -> None:
    _get_client().table("question_flags").upsert(
        {"user_id": user_id, "question_id": question_id},
        on_conflict="user_id,question_id",
    ).execute()


async def clear_history(user_id: int) -> None:
    _get_client().table("answers_log").delete().eq("user_id", user_id).execute()
