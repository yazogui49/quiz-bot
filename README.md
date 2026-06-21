# Telegram Quiz Bot — Setup Guide

## Stack
- **Bot runtime**: Python 3.12 + python-telegram-bot v21
- **Database**: Supabase (Postgres)
- **Hosting**: Railway (~$5/month, unlimited executions)

---

## Step 1 — Create the Supabase database

1. Go to [supabase.com](https://supabase.com) → your project → **SQL Editor**
2. Paste the contents of `sql/01_schema.sql` → **Run**
3. Confirm you see: `questions`, `users`, `answers_log`, `question_flags` tables + `unclear_questions` view

---

## Step 2 — Import your questions

1. Open `sql/02_import_questions.sql`
2. Replace the sample JSON array inside the single-quotes with the full contents of your questions file
3. Paste into the Supabase SQL Editor → **Run**
4. The last line returns the total count — confirm it matches your file

> `correct_answer` values are mapped automatically: `a→1 b→2 c→3 d→4`. Uppercase also works.

---

## Step 3 — Create the Telegram bot

1. Open Telegram → **@BotFather** → `/newbot`
2. Follow the prompts, copy the **API token** (looks like `123456789:AAF...`)

---

## Step 4 — Run locally (optional, to test before deploying)

```bash
cd quiz-bot
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and fill in your TELEGRAM_BOT_TOKEN and DATABASE_URL
# DATABASE_URL is in Supabase → Settings → Database → Connection string (URI)

python bot.py
```

Send `/start` to your bot in Telegram. You should receive the first question.

---

## Step 5 — Deploy to Railway

1. Push the `quiz-bot/` folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Select your repo
4. Railway auto-detects Python and installs `requirements.txt`
5. Go to your service → **Variables** → add:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `DATABASE_URL` = your Supabase connection string
6. Go to **Settings** → **Deploy** → set Start Command to `python bot.py`
7. Railway deploys and the bot goes live — no webhook needed, it polls Telegram

---

## Reviewing flagged questions

Run this in the Supabase SQL Editor at any time:

```sql
SELECT * FROM unclear_questions;
```

Shows all flagged questions sorted by how many users flagged each one.

---

## File structure

```
quiz-bot/
├── sql/
│   ├── 01_schema.sql           # Run once to create all tables
│   └── 02_import_questions.sql # Run when adding questions
├── bot.py                      # Telegram handlers + entry point
├── db.py                       # All database queries
├── requirements.txt
├── Procfile                    # For Railway
├── .env.example                # Copy to .env for local dev
├── .gitignore
└── README.md
```
