import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Message builders ──────────────────────────────────────────────────────────

_OPTION_KEY = {"1": "option_a", "2": "option_b", "3": "option_c", "4": "option_d"}

DONE_TEXT = "🎉 כל הכבוד! סיימת את כל השאלות.\nלחץ כדי להתחיל מחדש:"
DONE_KEYBOARD = InlineKeyboardMarkup(
    [[InlineKeyboardButton("התחל מחדש 🔄", callback_data="restart")]]
)


def _question_text(q: dict) -> str:
    return (
        f"<b>{q['question']}</b>\n\n"
        f"1. {q['option_a']}\n"
        f"2. {q['option_b']}\n"
        f"3. {q['option_c']}\n"
        f"4. {q['option_d']}\n\n"
        "מה התשובה הכי נכונה?"
    )


def _question_keyboard(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("1", callback_data=f"ans|1|{question_id}"),
                InlineKeyboardButton("2", callback_data=f"ans|2|{question_id}"),
                InlineKeyboardButton("3", callback_data=f"ans|3|{question_id}"),
                InlineKeyboardButton("4", callback_data=f"ans|4|{question_id}"),
            ],
            [InlineKeyboardButton("סמן שאלה כלא ברורה/מוזרה/לא נכונה/לא בחומר שלנו", callback_data=f"flag|{question_id}")],
        ]
    )


# ── Shared helper ─────────────────────────────────────────────────────────────

async def _send_next_or_done(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = await db.get_next_question(user_id)
    if q:
        await context.bot.send_message(
            chat_id=chat_id,
            text=_question_text(q),
            parse_mode="HTML",
            reply_markup=_question_keyboard(q["id"]),
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=DONE_TEXT,
            reply_markup=DONE_KEYBOARD,
        )


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)
    await _send_next_or_done(update.effective_chat.id, user_id, context)


async def on_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, answer, question_id_str = query.data.split("|")
    question_id = int(question_id_str)

    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)

    q = await db.get_question_by_id(question_id)
    if q is None:
        await query.message.reply_text("שגיאה: השאלה לא נמצאה.")
        return

    was_correct = answer == q["correct_answer"]
    await db.log_answer(user_id, question_id, was_correct)

    if was_correct:
        feedback = "✅ נכון! כל הכבוד!"
    else:
        correct_text = q[_OPTION_KEY[q["correct_answer"]]]
        feedback = f"❌ לא נכון. התשובה הנכונה היא:\n<b>{q['correct_answer']}. {correct_text}</b>"

    await query.message.reply_text(feedback, parse_mode="HTML")
    await _send_next_or_done(query.message.chat_id, user_id, context)


async def on_flag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("תודה על הדיווח 🙏")

    question_id = int(query.data.split("|")[1])

    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)

    await db.flag_question(user_id, question_id)
    await _send_next_or_done(query.message.chat_id, user_id, context)


async def on_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)

    await db.clear_history(user_id)
    await _send_next_or_done(query.message.chat_id, user_id, context)


async def on_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("שלח /start כדי להתחיל לשחק 🎮")


# ── Lifecycle ─────────────────────────────────────────────────────────────────

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    app = (
        Application.builder()
        .token(token)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(on_answer,  pattern=r"^ans\|"))
    app.add_handler(CallbackQueryHandler(on_flag,    pattern=r"^flag\|"))
    app.add_handler(CallbackQueryHandler(on_restart, pattern=r"^restart$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_unknown_message))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
