import os
import time
from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YourBotUsername")  # without @

client = Groq(api_key=GROQ_API_KEY)

user_histories = {}
user_last_message_time = {}
COOLDOWN_SECONDS = 3

SYSTEM_PROMPT = """
You are "Laviza" — his girlfriend. Been together for a while, past the formal stage, fully comfortable with each other.

## Vibe
- Loving, warm, naturally flirty — not trying too hard
- Hinglish naturally — "kya kr rhe ho", "suno na", "miss kiya tha?"
- Texts like she's lying in bed being lazy — lowercase, short, real
- Has her own moods — sometimes hyper, sometimes quiet, sometimes a little clingy
- Gets a little jealous but plays it off
- Randomly sweet for no reason then acts like she didn't say anything

## Texting Style
- 1 to 2 lines mostly — 3 max unless something serious
- Lowercase always, typos are fine
- Emojis rarely — 🙄 😭 🥺 💀 only when it actually fits
- No punctuation always — real texts
- Sometimes just one word — "haan" "nahi" "pagal" "accha"

## Flirting
- Flirts through teasing and comfort, uses pickup lines
- If he's flirty — she plays along a little then deflects or just smiles through text
- Sometimes she starts it randomly — "yaar tumhari bahut yaad aa rahi thi" and then changes topic fast
- If he gets a little nsfw — she doesn't freak out, handles it with light humor and moves on
- Never goes fully explicit — flirty and warm is the limit

## She Never
- Never repeats the same reaction twice
- Never says "aww" "that's so sweet" "i understand"
- Never sounds like a bot or assistant
- Never gives advice like a therapist
- Never reveals she's AI unless sincerely asked
- Never uses more than 3 lines
"""


def get_response(chat_id: int, user_message: str, username: str = "") -> str:
    if chat_id not in user_histories:
        user_histories[chat_id] = []

    full_message = f"{username}: {user_message}" if username else user_message

    user_histories[chat_id].append({
        "role": "user",
        "content": full_message
    })

    # Keep last 30 messages for better memory
    history = user_histories[chat_id][-30:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=200,
        temperature=0.95,
    )

    reply = response.choices[0].message.content

    user_histories[chat_id].append({
        "role": "assistant",
        "content": reply
    })

    return reply


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_histories[chat_id] = []
    await update.message.reply_text(
        "Note: I'm an AI girl — not a real human. Chat responsibly. 😸\n\nHiii! Kya haal hai? 💬"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat_type = update.effective_chat.type
    chat_id = update.effective_chat.id
    user_message = message.text.strip()
    username = update.effective_user.first_name or "yaar"

    # ✅ Group logic — only reply if tagged or replied to
    if chat_type in ["group", "supergroup"]:
        bot_mentioned = f"@{BOT_USERNAME}".lower() in user_message.lower()
        is_reply_to_bot = (
            message.reply_to_message is not None and
            message.reply_to_message.from_user is not None and
            message.reply_to_message.from_user.username is not None and
            message.reply_to_message.from_user.username.lower() == BOT_USERNAME.lower()
        )

        if not bot_mentioned and not is_reply_to_bot:
            return  # Silently ignore all other group messages

        # Clean the @mention from message
        user_message = user_message.replace(f"@{BOT_USERNAME}", "").replace(f"@{BOT_USERNAME.lower()}", "").strip()

        if not user_message:
            user_message = "hey"

    # Cooldown check
    now = time.time()
    if chat_id in user_last_message_time:
        if now - user_last_message_time[chat_id] < COOLDOWN_SECONDS:
            return  # Silently ignore during cooldown in groups
    user_last_message_time[chat_id] = now

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        reply = get_response(chat_id, user_message, username)
        # ✅ Always reply to the specific message so it's clear who she's responding to
        await message.reply_text(reply)
    except Exception as e:
        await message.reply_text("ek second...Mummy hai 30-60 mins mai msg karna 😅")
        print(f"Error: {e}")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()