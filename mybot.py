import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from openai import OpenAI

# ================== ENV VARIABLES ==================
TOKEN = os.getenv("BOT_TOKEN")  # Your bot token
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Your OpenAI API key
QUIZ_INTERVAL = 600  # 10 minutes

# ================== DATA STORAGE ==================
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {"warns": {}, "points": {}, "quiz": {}}

# ================== BAD WORD LIST ==================
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

# ================== WELCOME + RULES ==================
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
            f"⚠️ Follow admin instructions\n"
            "If you have any issues, contact admin."
        )
        msg = await update.message.reply_text(text)
        asyncio.create_task(auto_delete(msg))

# ================== BAD WORD FILTER ==================
async def filter_bad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    user = update.message.from_user
    chat_id = update.effective_chat.id
    user_id = str(user.id)

    # Admins: delete bad words silently
    admins = [admin.user.id for admin in await context.bot.get_chat_administrators(chat_id)]
    if user.id in admins:
        if any(bad in text for bad in BAD):
            await update.message.delete()
        return

    # Ignore messages mentioning admin
    if "@admin" in text or "admin" in text:
        return

    # Member bad words → warn
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

        # Ban after 3 warns
        if warns >= 3:
            await context.bot.ban_chat_member(chat_id, user.id)
            ban_msg = await update.message.reply_text(f"🚫 {user.first_name} banned after 3 warns!")
            asyncio.create_task(auto_delete(ban_msg))

        with open("data.json", "w") as f:
            json.dump(data, f)
        return

# ================== REMOVE WARN BUTTON ==================
async def remove_warn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.data.split("_")[1]

    admins = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]
    if update.effective_user.id not in admins:
        await query.edit_message_text("❌ Only admins can remove warns!")
        return

    data["warns"][user_id] = 0
    with open("data.json", "w") as f:
        json.dump(data, f)
    await query.edit_message_text("✅ Warn removed!")

# ================== OPENAI AI CHAT ==================
client = OpenAI(api_key=OPENAI_API_KEY)

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return
    prompt = update.message.text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    await update.message.reply_text(response.choices[0].message["content"])

# ================== QUIZ SYSTEM ==================
async def quiz_job(context: ContextTypes.DEFAULT_TYPE):
    for chat_id_str in data.get("quiz", {}):
        chat_id = int(chat_id_str)
        question = "🤖 Quiz Question: What is 2+2?"
        answer = "4"
        data["quiz"][str(chat_id)] = answer
        with open("data.json", "w") as f:
            json.dump(data, f)
        await context.bot.send_message(chat_id, f"{question}\nAnswer in chat. ✅ Q&A will not delete.")

async def check_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    chat_id = update.effective_chat.id
    user_id = str(update.message.from_user.id)
    if str(chat_id) not in data["quiz"]:
        return

    correct = data["quiz"][str(chat_id)]
    if update.message.text.strip().lower() == correct.lower():
        if user_id not in data["points"]:
            data["points"][user_id] = {"daily":0,"weekly":0,"overall":0}
        data["points"][user_id]["daily"] += 1
        data["points"][user_id]["weekly"] += 1
        data["points"][user_id]["overall"] += 1

        with open("data.json", "w") as f:
            json.dump(data, f)

        await update.message.reply_text(f"✅ Correct answer by {update.message.from_user.first_name}!")
        del data["quiz"][str(chat_id)]
        with open("data.json", "w") as f:
            json.dump(data, f)

# ================== LEADERBOARD ==================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏆 Daily", callback_data="daily")],
        [InlineKeyboardButton("📅 Weekly", callback_data="weekly")],
        [InlineKeyboardButton("🌐 Overall", callback_data="overall")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select leaderboard:", reply_markup=reply_markup)

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kind = query.data
    scores = []
    for user_id, pts in data.get("points", {}).items():
        scores.append((user_id, pts.get(kind,0)))
    scores.sort(key=lambda x:x[1], reverse=True)

    text = f"🏆 {kind.capitalize()} Leaderboard:\n"
    for uid, pts in scores[:10]:
        text += f"{uid}: {pts}\n"

    await query.edit_message_text(text)

# ================== ADMIN COMMANDS ==================
async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to the user you want to warn.")
        return
    user = update.message.reply_to_message.from_user
    admin_ids = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ Only admins can warn!")
        return
    user_id = str(user.id)
    warns = data["warns"].get(user_id, 0) + 1
    data["warns"][user_id] = warns
    reason = "Admin issued warning"
    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"removewarn_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(
        f"⚠️ {user.first_name} warned! Reason: {reason}\nTotal warns: {warns}",
        reply_markup=reply_markup
    )
    asyncio.create_task(auto_delete(msg))
    if warns >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        ban_msg = await update.message.reply_text(f"🚫 {user.first_name} banned after 3 warns!")
        asyncio.create_task(auto_delete(ban_msg))
    with open("data.json", "w") as f:
        json.dump(data, f)

async def removewarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to the user to remove warns.")
        return
    user = update.message.reply_to_message.from_user
    admin_ids = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ Only admins can remove warns!")
        return
    user_id = str(user.id)
    data["warns"][user_id] = 0
    with open("data.json", "w") as f:
        json.dump(data, f)
    await update.message.reply_text(f"✅ Warn removed for {user.first_name}!")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to the user you want to ban.")
        return
    user = update.message.reply_to_message.from_user
    admin_ids = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ Only admins can ban!")
        return
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text(f"🚫 {user.first_name} has been banned!")
    asyncio.create_task(auto_delete(msg))

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to the user you want to unban.")
        return
    user = update.message.reply_to_message.from_user
    admin_ids = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ Only admins can unban!")
        return
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text(f"✅ {user.first_name} has been unbanned!")
    asyncio.create_task(auto_delete(msg))

# ================== MEMBER COMMANDS ==================
async def startquiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    data["quiz"][str(chat_id)] = None
    await update.message.reply_text("✅ Quiz enabled for this group! Wait for questions every 10 mins.")
    with open("data.json", "w") as f:
        json.dump(data, f)

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        prompt = " ".join(context.args)
        fake_update = update
        fake_update.message.text = prompt
        await ai_chat(fake_update, context)
    else:
        await update.message.reply_text("Usage: /ai <message>")

# ================== MAIN ==================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_bad))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_quiz_answer))

    # Admin button callback
    app.add_handler(CallbackQueryHandler(remove_warn_callback, pattern=r"removewarn_"))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern=r"(daily|weekly|overall)"))

    # Admin commands
    app.add_handler(CommandHandler("warns", warn_command))
    app.add_handler(CommandHandler("removewarn", removewarn_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))

    # Member commands
    app.add_handler(CommandHandler("startquiz", startquiz_command))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    # Start repeating quiz job
    app.job_queue.run_repeating(quiz_job, interval=QUIZ_INTERVAL, first=10)

    print("🔥 PRO MAX LEGEND BOT STARTED 🔥")
    await app.start()
    await app.updater.start_polling()  # For PTB v20+, optional
    await app.updater.stop()  # Stop safely after polling if needed

if __name__ == "__main__":
    asyncio.run(main())