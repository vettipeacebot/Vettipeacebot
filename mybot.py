import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from openai import OpenAI

# ================== ENV ==================
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QUIZ_INTERVAL = 600  # 10 mins

# ================== DATA ==================
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {"warns": {}, "points": {}, "quiz": {}}

# ================== BAD WORDS ==================
BAD = [
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
    "pm","dm","private chat","private message","direct chat","direct message",
    "punda","sunni","potta","thevudiya","thayoli","oombu","nudity","thevidya",
    "ummbu","gommala","ommala","kotta","badu","pvrt","ummbi","thayali","aatha","otha"
]

# ================== AUTO DELETE ==================
async def auto_delete(msg, delay=180):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

# ================== WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        name = user.first_name
        username = f"@{user.username}" if user.username else "No username"
        chat_id = update.effective_chat.id

        text = (
            f"🔮 Welcome to Bun Butter Jam!\n"
            f"👤 Name: {name}\n"
            f"💬 Username: {username}\n"
            f"🆔 Group ID: {chat_id}\n\n"
            f"📜 Rules:\n"
            f"📩 Don't PM/DM others\n"
            f"🚫 Avoid bad words\n"
            f"⚠️ Follow admin instructions"
        )
        msg = await update.message.reply_text(text)
        asyncio.create_task(auto_delete(msg))

# ================== FILTER BAD WORDS ==================
async def filter_bad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    user = update.message.from_user
    chat = update.effective_chat
    user_id = str(user.id)

    # Only get admins in groups/supergroups
    admins = []
    if chat.type in ["group", "supergroup"]:
        try:
            admins = [a.user.id for a in await context.bot.get_chat_administrators(chat.id)]
        except:
            admins = []

    if user.id in admins:
        if any(bad in text for bad in BAD):
            await update.message.delete()
        return

    if "@admin" in text or "admin" in text:
        return

    if any(bad in text for bad in BAD):
        await update.message.delete()
        warns = data["warns"].get(user_id, 0) + 1
        data["warns"][user_id] = warns
        reason = "Against the group rules"

        keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"removewarn_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg = await update.message.reply_text(
            f"⚠️ {user.first_name} warned! Reason: {reason}\nTotal warns: {warns}",
            reply_markup=reply_markup
        )
        asyncio.create_task(auto_delete(msg))

        if warns >= 3 and chat.type in ["group", "supergroup"]:
            await context.bot.ban_chat_member(chat.id, user.id)
            ban_msg = await update.message.reply_text(f"🚫 {user.first_name} banned after 3 warns!")
            asyncio.create_task(auto_delete(ban_msg))

        with open("data.json", "w") as f:
            json.dump(data, f)

# ================== REMOVE WARN BUTTON ==================
async def remove_warn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.data.split("_")[1]

    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await query.edit_message_text("❌ This command only works in groups.")
        return

    admins = [a.user.id for a in await context.bot.get_chat_administrators(chat.id)]
    if update.effective_user.id not in admins:
        await query.edit_message_text("❌ Only admins can remove warns!")
        return

    data["warns"][user_id] = 0
    with open("data.json", "w") as f:
        json.dump(data, f)
    await query.edit_message_text("✅ Warn removed!")

# ================== OPENAI CHAT ==================
client = OpenAI(api_key=OPENAI_API_KEY)

async def ai_chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    prompt = " ".join(context.args) if context.args else update.message.text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    await update.message.reply_text(response.choices[0].message["content"])

# ================== QUIZ ==================
async def start_quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if str(chat.id) in data["quiz"]:
        await update.message.reply_text("❌ Quiz already running in this chat.")
        return

    question = "🤖 Quiz Question: What is 2+2?"
    answer = "4"
    data["quiz"][str(chat.id)] = answer
    with open("data.json", "w") as f:
        json.dump(data, f)
    await update.message.reply_text(f"{question}\nAnswer in chat. ✅ Q&A will not delete.")

async def quiz_job(context: ContextTypes.DEFAULT_TYPE):
    for chat_id_str in list(data.get("quiz", {})):
        chat_id = int(chat_id_str)
        question = "🤖 Quiz Question: What is 2+2?"
        answer = "4"
        data["quiz"][chat_id_str] = answer
        with open("data.json", "w") as f:
            json.dump(data, f)
        await context.bot.send_message(chat_id, f"{question}\nAnswer in chat. ✅ Q&A will not delete.")

async def check_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_id = str(update.message.from_user.id)
    if chat_id not in data.get("quiz", {}):
        return
    correct = data["quiz"][chat_id]
    if update.message.text.strip().lower() == correct.lower():
        if user_id not in data["points"]:
            data["points"][user_id] = {"daily":0,"weekly":0,"overall":0}
        data["points"][user_id]["daily"] += 1
        data["points"][user_id]["weekly"] += 1
        data["points"][user_id]["overall"] += 1
        await update.message.reply_text(f"✅ Correct answer by {update.message.from_user.first_name}!")
        del data["quiz"][chat_id]
        with open("data.json", "w") as f:
            json.dump(data, f)

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_bad))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_quiz_answer))

    # Commands
    app.add_handler(CommandHandler("ai", ai_chat_cmd))
    app.add_handler(CommandHandler("startquiz", start_quiz_cmd))

    # Remove warn button
    app.add_handler(CallbackQueryHandler(remove_warn_callback, pattern=r"removewarn_"))

    # Quiz repeating
    app.job_queue.run_repeating(quiz_job, interval=QUIZ_INTERVAL, first=10)

    print("🔥 PRO MAX LEGEND BOT STARTED 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()