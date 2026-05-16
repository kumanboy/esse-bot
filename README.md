# Essay Checker Telegram Bot

Essay Checker Telegram Bot is a Python-based Telegram bot for checking Uzbek essays according to the **UZBMB essay evaluation system**. It is used as the continuation of the 45th essay question in the Certification Project.

The bot allows students to submit an essay topic and essay text, checks the essay using OpenAI based on a strict Uzbek national certification rubric, sends the AI evaluation to the teacher/admin, and then delivers teacher voice feedback to the student after admin review.

---

## Table of Contents

1. [Project Purpose](#project-purpose)
2. [Main Features](#main-features)
3. [Tech Stack](#tech-stack)
4. [Bot Flow](#bot-flow)
5. [Database Schema](#database-schema)
6. [Project Structure](#project-structure)
7. [Installation](#installation)
8. [Environment Variables](#environment-variables)
9. [Running Locally](#running-locally)
10. [Docker Deployment](#docker-deployment)
11. [Essay Checking Logic](#essay-checking-logic)
12. [Payment and Balance System](#payment-and-balance-system)
13. [Admin Voice Feedback Workflow](#admin-voice-feedback-workflow)
14. [Useful Commands](#useful-commands)
15. [Security Notes](#security-notes)
16. [Future Improvements](#future-improvements)

---

## Project Purpose

The main goal of this bot is to help students check their essays based on the **UZBMB essay evaluation criteria**.

The bot is connected with the main Certification Website. In the website, question 45 directs students to this Telegram bot for essay checking.

The system is designed for:

- Uzbek language and literature exam preparation;
- Milliy Sertifikat-style essay evaluation;
- automated first evaluation using OpenAI;
- teacher/admin voice feedback;
- payment-based essay checking;
- one-time free essay checking for new subscribed users.

---

## Main Features

The bot supports:

- Telegram-based essay submission;
- required channel subscription check;
- one-time free essay check;
- balance/credit system;
- payment receipt submission;
- admin payment approval/rejection;
- UZBMB-based essay evaluation using OpenAI;
- essay length validation;
- admin voice feedback workflow;
- delayed voice feedback delivery;
- admin recovery commands for essay feedback;
- PostgreSQL persistence;
- Docker deployment.

---

## Tech Stack

- **Python 3.11**
- **Aiogram**
- **OpenAI Python SDK**
- **PostgreSQL 16**
- **asyncpg**
- **APScheduler**
- **python-dotenv**
- **Docker Compose**

---

## Bot Flow

### 1. User starts the bot

The user sends:

```text
/start
```

The bot checks whether the user is subscribed to the required Telegram channel.

If the user is not subscribed, the bot shows a subscription message and a check button.

If the user is subscribed, the bot checks whether the user has already used the free try.

If not used, the bot gives 1 free essay-checking credit.

---

### 2. User submits an essay

The user clicks:

```text
📝 Esse tekshirish
```

The bot checks:

- whether the user is locked because another essay is still being checked;
- whether the user has at least 1 balance;
- whether the essay topic is provided;
- whether the essay text is provided;
- whether the essay has at least 100 words;
- whether the essay is not longer than 350 words.

If the essay is valid, the bot consumes 1 balance and starts the essay checking workflow.

---

### 3. OpenAI checks the essay

The essay is checked using a strict UZBMB rubric prompt.

The result is not sent directly to the student. Instead, the AI result is sent to the essay admin.

---

### 4. Admin sends voice feedback

The admin replies to the essay result message with a Telegram voice message.

The bot saves the voice `file_id` and schedules it to be sent to the user after 30 minutes.

---

### 5. Student receives voice feedback

After the scheduled delay, the bot sends the admin voice feedback to the student and unlocks the user so the student can submit another essay later.

---

## Database Schema

Main schema file:

```text
schema.sql
```

The bot uses the following tables:

### users

Stores Telegram users.

Important columns:

```text
user_id
created_at
```

### balances

Stores the number of essay-checking credits for each user.

Important columns:

```text
user_id
balance
updated_at
```

### free_tries

Stores whether a user has already received the one-time free essay check.

Important columns:

```text
user_id
used_at
```

### payments

Stores payment receipt submissions and admin decisions.

Important columns:

```text
payment_id
user_id
amount
status
username
receipt_kind
receipt_file_id
created_at
decided_at
decided_by
```

Payment statuses:

```text
pending
approved
rejected
```

Receipt types:

```text
photo
document
```

### essay_reviews

Stores submitted essays, OpenAI result, admin voice feedback, and status.

Important columns:

```text
essay_id
user_id
topic
essay_text
ai_result
admin_chat_id
admin_msg_id
voice_file_id
status
created_at
voiced_at
sent_to_user_at
voice_sent_at
voice_sent_by
voice_msg_id
```

Essay review statuses:

```text
waiting_voice
voice_scheduled
voice_sent
resent
completed
```

---

## Project Structure

Example structure:

```text
bot/
  config.py
  main.py
  states.py

  handlers/
    essay.py
    payment.py
    subscription.py
    admin.py
    admin_recovery.py
    admin_voice.py
    help.py
    start.py

  services/
    db.py
    balance.py
    payments.py
    essay_checker.py
    scheduler.py
    locks.py
    subscription.py
    permissions.py
    word_count.py

  keyboards/
    main.py
    payment.py
    subscribe.py
    admin.py

requirements.txt
schema.sql
Dockerfile
docker-compose.yml
README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/kumanboy/esse-bot.git
cd esse-bot
```

Replace the repository URL with the actual essay bot repository URL if it is different.

### 2. Create virtual environment

```bash
python -m venv .venv
```

Activate it:

On Linux/macOS:

```bash
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root.

Example:

```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5-mini
ADMIN_ID=123456789
MONEY_ID=123456789
DATABASE_URL=postgresql://postgres:0011@localhost:5432/essebot
DEBUG_OPENAI=0
```

### Variable explanation

| Variable | Purpose |
|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `OPENAI_API_KEY` | OpenAI API key for essay checking |
| `OPENAI_MODEL` | OpenAI model name, default is `gpt-5-mini` |
| `ADMIN_ID` | Essay admin Telegram user ID |
| `MONEY_ID` | Payment admin Telegram user ID |
| `DATABASE_URL` | PostgreSQL connection string |
| `DEBUG_OPENAI` | Optional debug flag for OpenAI response logging |

Do not commit `.env` to GitHub.

---

## Running Locally

### 1. Start PostgreSQL

You can start the database through Docker:

```bash
docker compose up -d postgres
```

### 2. Run schema

```bash
docker exec -i esse_postgres psql -U postgres -d essebot < schema.sql
```

### 3. Run the bot

```bash
python -m bot.main
```

If everything is configured correctly, the bot starts polling Telegram updates.

---

## Docker Deployment

The project includes Docker support.

Build and start:

```bash
docker compose up -d --build
```

Check containers:

```bash
docker compose ps
```

View bot logs:

```bash
docker compose logs esse_bot --tail=200
```

View database logs:

```bash
docker compose logs esse_postgres --tail=200
```

Stop services:

```bash
docker compose down
```

---

## Docker Compose Services

The bot uses two services:

### postgres

Container name:

```text
esse_postgres
```

Purpose:

```text
PostgreSQL database for users, balances, payments, and essay reviews.
```

### bot

Container name:

```text
esse_bot
```

Purpose:

```text
Runs the Telegram bot using python -m bot.main.
```

---

## Essay Checking Logic

Main file:

```text
bot/services/essay_checker.py
```

The bot sends the essay topic and essay text to OpenAI with a strict UZBMB-based rubric prompt.

The rubric checks:

- publitsistik style;
- two opposing views;
- personal opinion;
- arguments and evidence;
- introduction, body, and conclusion;
- paragraph structure;
- logical consistency;
- spelling;
- punctuation;
- suffix usage;
- word usage;
- lexical richness;
- speech purity.

The evaluation uses 12 criteria, each scored from 0 to 2:

```text
2
1.5
1
0.5
0
```

The maximum score is:

```text
24 points
```

The bot also converts the result to a 75-point scale using the official lookup matrix defined in the rubric prompt.

---

## Essay Length Rules

Main file:

```text
bot/services/word_count.py
```

Word counting uses a regular expression and supports Uzbek apostrophe forms such as:

```text
o‘
g‘
o`
g`
```

Rules:

- essay under 100 words is rejected with 2 points;
- essay over 350 words is rejected;
- only text essays are accepted;
- numbers and emojis are not counted as words.

---

## Payment and Balance System

Main files:

```text
bot/handlers/payment.py
bot/handlers/admin.py
bot/services/payments.py
bot/services/balance.py
```

### Payment flow

1. User clicks:

```text
💳 Hisobni to‘ldirish
```

2. Bot sends payment instructions.
3. User sends receipt as photo or document.
4. Bot creates a pending payment record.
5. Receipt is sent to payment admin.
6. Admin approves or rejects using inline buttons.
7. If approved, user balance increases.
8. If rejected, user receives rejection message.

### Balance flow

Balance represents essay-checking credits.

Important functions:

```text
get_balance()
add_balance()
consume_balance()
refund_balance()
grant_free_balance()
has_used_free()
```

`consume_balance()` uses a database transaction and `FOR UPDATE`, which prevents double spending of the same balance.

---

## Free Try System

Every subscribed user can receive exactly one free essay check.

Main files:

```text
bot/handlers/subscription.py
bot/services/balance.py
```

The bot records free try usage in:

```text
free_tries
```

This prevents repeated free usage.

---

## Subscription Check

Main file:

```text
bot/services/subscription.py
```

The bot checks whether the user is subscribed to the required Telegram channel:

```text
@sardortoshmuhammad_onatili
```

Accepted Telegram statuses:

```text
MEMBER
ADMINISTRATOR
CREATOR
```

If Telegram returns an error or the bot cannot verify membership, the user is treated as not subscribed.

---

## Admin Voice Feedback Workflow

Main files:

```text
bot/handlers/admin_voice.py
bot/handlers/admin_recovery.py
bot/services/scheduler.py
bot/services/locks.py
```

### Normal voice workflow

1. AI result is sent to the essay admin.
2. Admin replies to the anchor message with a voice message.
3. Bot finds the related essay using `admin_chat_id` and `admin_msg_id`.
4. Bot saves `voice_file_id` to `essay_reviews`.
5. Essay status becomes `voice_scheduled`.
6. APScheduler schedules the voice message.
7. After 30 minutes, the bot sends the voice feedback to the student.
8. Essay status becomes `voice_sent`.
9. The user is unlocked.

---

## Admin Recovery Commands

Main file:

```text
bot/handlers/admin_recovery.py
```

Available commands:

### Reset essay voice state

```text
/fix <essay_id>
```

Resets essay status to `waiting_voice` and clears voice fields.

### Resend voice feedback

```text
/resend <essay_id>
```

Resends the saved voice feedback to the user.

### Cancel voice feedback

```text
/cancel <essay_id>
```

Cancels voice feedback, clears voice data, resets status, and unlocks the user.

---

## User Lock System

Main file:

```text
bot/services/locks.py
```

The bot uses an in-memory lock:

```python
active_checks: set[int] = set()
```

This prevents a user from submitting another essay while the previous essay is still waiting for result or teacher voice feedback.

Important note:

```text
The lock is in-memory, so it resets if the bot container restarts.
```

Future improvement: move the lock system to PostgreSQL or infer active locks from `essay_reviews.status`.

---

## Scheduler

Main file:

```text
bot/services/scheduler.py
```

The bot uses:

```text
AsyncIOScheduler
```

Scheduler is used for:

- delayed essay checking jobs;
- delayed admin voice delivery.

The scheduler starts in:

```text
bot/main.py
```

---

## Admin Roles

Main files:

```text
bot/config.py
bot/services/permissions.py
```

The bot separates two admin roles:

| Role | Variable | Purpose |
|---|---|---|
| Essay Admin | `ADMIN_ID` | Receives AI result and sends voice feedback |
| Payment Admin | `MONEY_ID` | Approves or rejects payment receipts |

---

## Useful Commands

Start all Docker services:

```bash
docker compose up -d --build
```

Check logs:

```bash
docker compose logs esse_bot --tail=200
```

Enter PostgreSQL:

```bash
docker compose exec postgres psql -U postgres -d essebot
```

Show tables:

```sql
\dt
```

Count essay reviews:

```sql
SELECT COUNT(*) FROM essay_reviews;
```

Show pending payments:

```sql
SELECT payment_id, user_id, amount, status, created_at
FROM payments
ORDER BY created_at DESC
LIMIT 10;
```

Show waiting voice essays:

```sql
SELECT essay_id, user_id, status, created_at
FROM essay_reviews
WHERE status = 'waiting_voice'
ORDER BY created_at DESC;
```

---

## Security Notes

Do not commit real secrets:

```text
BOT_TOKEN
OPENAI_API_KEY
DATABASE_URL
ADMIN_ID
MONEY_ID
```

Do not commit `.env`.

Recommended `.gitignore`:

```gitignore
.env
.venv
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.idea/
.vscode/
```

Payment card details should be stored carefully and should not be exposed in public documentation.

---

## Connection to Certification Website

The main Certification Website uses question 45 as the essay section and sends students to this bot.

Website route:

```text
/exam
```

Essay bot link:

```text
https://t.me/esse_tekshir_bot
```

Together, the system works as:

```text
Certification Website → Question 45 → Telegram Essay Bot → UZBMB essay checking → Teacher voice feedback
```

---

## Future Improvements

Recommended improvements:

- move in-memory locks to PostgreSQL;
- add persistent scheduled job recovery after bot restart;
- add admin dashboard for essay reviews;
- add automatic cleanup for old payments and reviews;
- add better payment provider integration;
- add user history command;
- add essay review PDF export;
- add detailed statistics for essays;
- add more robust moderation and spam protection.

---

## Final Summary

Essay Checker Telegram Bot is a production-oriented Telegram assistant for Uzbek essay evaluation. It combines OpenAI-based UZBMB rubric checking, teacher voice feedback, payment verification, free trial logic, balance management, PostgreSQL storage, and Docker deployment.

It works as the essay-checking extension of the Certification Project and strengthens the overall diploma system by adding a practical AI-assisted essay evaluation workflow.
