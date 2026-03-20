import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from openai import OpenAI

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ================= DATA =================
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {"warns": {}}

# ================= BAD WORDS =================
BAD = [
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
    "pm","dm","private chat","private message","direct chat","direct message",
    "punda","sunni","potta","thevudiya","thayoli","oombu","nudity","inbox","thevidya","ummbu","gommala","ommala","kotta","badu","pvrt","ummbi","thayali","aatha","otha"
]
       
# ================= AUTO DELETE =================
async def auto_delete(msg, delay=180):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

# ================= ADMIN CHECK =================
async def is_admin(update, context):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return update.effective_user.id in [a.user.id for a in admins]
    except:
        return False

# ================= WELCOME =================
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
        )

        msg = await update.message.reply_text(text)
        asyncio.create_task(auto_delete(msg))

# ================= BAD WORD FILTER =================
async def filter_bad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user = update.message.from_user
    user_id = str(user.id)

    if await is_admin(update, context):
        return

    if any(word in text for word in BAD):
        await update.message.delete()

        warns = data["warns"].get(user_id, 0) + 1
        data["warns"][user_id] = warns

        keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{user_id}")]]
        msg = await update.message.reply_text(
            f"⚠️ {user.first_name} warned\nReason: against group rules\nTotal: {warns}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        asyncio.create_task(auto_delete(msg))

        if warns >= 3:
            await context.bot.ban_chat_member(update.effective_chat.id, user.id)
            m = await update.message.reply_text("🚫 User banned (3 warns)")
            asyncio.create_task(auto_delete(m))

        with open("data.json", "w") as f:
            json.dump(data, f)

# ================= REMOVE WARN BUTTON =================
async def remove_warn_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_admin(update, context):
        await query.edit_message_text("❌ Admin only")
        return

    user_id = query.data.split("_")[1]
    data["warns"][user_id] = 0

    with open("data.json", "w") as f:
        json.dump(data, f)

    await query.edit_message_text("✅ Warn removed")

# ================= AI =================
async def ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Use: /ai your question")

    prompt = " ".join(context.args)

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    msg = await update.message.reply_text(res.choices[0].message.content)
    asyncio.create_task(auto_delete(msg))

# ================= ADMIN COMMANDS =================

# /warn @user reason
async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admin only")

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to user to warn")

    user = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "No reason"

    uid = str(user.id)
    warns = data["warns"].get(uid, 0) + 1
    data["warns"][uid] = warns

    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{uid}")]]
    msg = await update.message.reply_text(
        f"⚠️ {user.first_name} warned\nReason: {reason}\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(msg))

    if warns >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        m = await update.message.reply_text("🚫 User banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# /removewarn
async def removewarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    data["warns"][str(user.id)] = 0

    msg = await update.message.reply_text("✅ Warn removed")
    asyncio.create_task(auto_delete(msg))

# /ban
async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)

    msg = await update.message.reply_text("🚫 Banned")
    asyncio.create_task(auto_delete(msg))

# /unban
async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)

    msg = await update.message.reply_text("✅ Unbanned")
    asyncio.create_task(auto_delete(msg))

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_bad))
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    app.add_handler(CommandHandler("ai", ai))
    app.add_handler(CommandHandler("warns", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    print("🔥 BOT RUNNING 🔥")

    # ✅ THIS handles event loop internally
    app.run_polling()


if __name__ == "__main__":
    main()