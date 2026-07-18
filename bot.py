import logging
import os

from dotenv import load_dotenv
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
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
DONE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("התחל מחדש 🔄", callback_data="restart")],
    [InlineKeyboardButton("🎯 מצב מבחן (26 שאלות)", callback_data="start_test")],
    [InlineKeyboardButton("📊 הביצועים שלי לפי נושא", callback_data="stats")],
])


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
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1", callback_data=f"ans|1|{question_id}"),
            InlineKeyboardButton("2", callback_data=f"ans|2|{question_id}"),
            InlineKeyboardButton("3", callback_data=f"ans|3|{question_id}"),
            InlineKeyboardButton("4", callback_data=f"ans|4|{question_id}"),
        ],
        [
            InlineKeyboardButton("לא ברורה", callback_data=f"flag|{question_id}|unclear"),
            InlineKeyboardButton("לא נכונה", callback_data=f"flag|{question_id}|wrong"),
            InlineKeyboardButton("לא בחומר", callback_data=f"flag|{question_id}|off_topic"),
        ],
    ])


def _test_question_keyboard(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1", callback_data=f"ans|1|{question_id}"),
            InlineKeyboardButton("2", callback_data=f"ans|2|{question_id}"),
            InlineKeyboardButton("3", callback_data=f"ans|3|{question_id}"),
            InlineKeyboardButton("4", callback_data=f"ans|4|{question_id}"),
        ],
    ])


# ── Stats helpers ─────────────────────────────────────────────────────────────

async def _send_stats(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    stats = await db.get_topic_stats(user_id)
    if not stats:
        await context.bot.send_message(chat_id=chat_id, text="עדיין לא ענית על שאלות. שלח /start כדי להתחיל!")
        return
    total_answered = sum(int(r["total"]) for r in stats)
    total_correct = sum(int(r["correct"]) for r in stats)
    total_pct = round(100 * total_correct / total_answered) if total_answered else 0
    lines = [
        f"📊 <b>הביצועים שלך</b>\n"
        f"סה\"כ: {total_correct}/{total_answered} ({total_pct}%)\n"
        f"─────────────────\n"
    ]
    for row in stats:
        pct = int(row["pct"])
        emoji = "✅" if pct >= 70 else "⚠️" if pct >= 50 else "❌"
        lines.append(f"{emoji} <b>{row['topic']}</b>\n{row['correct']}/{row['total']} ({pct}%)\n")
    await context.bot.send_message(chat_id=chat_id, text="\n".join(lines), parse_mode="HTML")


async def _send_test_summary(chat_id: int, results: list, context: ContextTypes.DEFAULT_TYPE) -> None:
    total = len(results)
    correct_total = sum(1 for r in results if r["was_correct"])
    pct_total = round(100 * correct_total / total) if total else 0

    lines = [f"📝 <b>תוצאות המבחן</b>\nציון כולל: {correct_total}/{total} ({pct_total}%)\n"]

    wrong = [r for r in results if not r["was_correct"]]
    if wrong:
        lines.append("❌ <b>שאלות שטעית בהן:</b>\n")
        for r in wrong:
            q = r["q"]
            correct_text = q[_OPTION_KEY[q["correct_answer"]]]
            lines.append(
                f"• <b>{q['question']}</b>\n"
                f"  התשובה הנכונה: {q['correct_answer']}. {correct_text}\n"
            )
    else:
        lines.append("🌟 מושלם! ענית נכון על הכל!")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 מבחן נוסף", callback_data="start_test")],
        [InlineKeyboardButton("📚 חזור ללמוד", callback_data="restart")],
    ])
    await context.bot.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ── Shared helpers ────────────────────────────────────────────────────────────

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


async def _start_test(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    questions = await db.get_test_questions(user_id)
    if not questions:
        await context.bot.send_message(chat_id=chat_id, text="אין מספיק שאלות שלא ענית עליהן כדי להתחיל מבחן. נסה /start ללמוד קודם!")
        return
    context.user_data["test"] = {"questions": questions, "answered": 0, "results": []}
    first = questions[0]
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🎯 <b>מצב מבחן — {len(questions)} שאלות</b>\nענה על כל השאלות ובסוף תקבל סיכום.\n💡 ניתן לשנות תשובה על שאלה שכבר ענית — פשוט גלול למעלה ולחץ שוב.\n\nשאלה 1/{len(questions)}:\n\n" + _question_text(first),
        parse_mode="HTML",
        reply_markup=_test_question_keyboard(first["id"]),
    )


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)
    await _send_stats(update.effective_chat.id, user_id, context)


async def on_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)
    await _send_stats(query.message.chat_id, user_id, context)


async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)
    await _start_test(update.effective_chat.id, user_id, context)


async def on_start_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)
    await _start_test(query.message.chat_id, user_id, context)


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

    test = context.user_data.get("test")

    if test is not None:
        q = next((q for q in test["questions"] if q["id"] == question_id), None)
        if q is None:
            await query.message.reply_text("שגיאה: השאלה לא נמצאה.")
            return

        was_correct = answer == q["correct_answer"]
        await db.log_answer(user_id, question_id, was_correct)

        # If already answered, update result in summary but don't send a new question
        existing = next((i for i, r in enumerate(test["results"]) if r["q"]["id"] == question_id), None)
        if existing is not None:
            test["results"][existing] = {"topic": q["topic"], "was_correct": was_correct, "q": q}
            return

        test["results"].append({"topic": q["topic"], "was_correct": was_correct, "q": q})
        test["answered"] += 1

        if test["answered"] < len(test["questions"]):
            next_q = test["questions"][test["answered"]]
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"שאלה {test['answered'] + 1}/{len(test['questions'])}:\n\n" + _question_text(next_q),
                parse_mode="HTML",
                reply_markup=_test_question_keyboard(next_q["id"]),
            )
        else:
            results = test["results"]
            del context.user_data["test"]
            await _send_test_summary(query.message.chat_id, results, context)

    else:
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

    parts = query.data.split("|")
    question_id = int(parts[1])
    reason = parts[2] if len(parts) > 2 else "unclear"

    user = update.effective_user
    user_id = await db.upsert_user(user.id, user.first_name)

    await db.flag_question(user_id, question_id, reason)
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

async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("start", "התחל ללמוד — שאלה אחר שאלה"),
        BotCommand("test", "מצב מבחן — 26 שאלות עם סיכום בסוף"),
        BotCommand("stats", "הביצועים שלי לפי נושא"),
    ])


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    app = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("test", cmd_test))
    app.add_handler(CallbackQueryHandler(on_answer,     pattern=r"^ans\|"))
    app.add_handler(CallbackQueryHandler(on_flag,       pattern=r"^flag\|"))
    app.add_handler(CallbackQueryHandler(on_restart,    pattern=r"^restart$"))
    app.add_handler(CallbackQueryHandler(on_stats,      pattern=r"^stats$"))
    app.add_handler(CallbackQueryHandler(on_start_test, pattern=r"^start_test$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_unknown_message))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
