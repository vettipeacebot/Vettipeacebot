import os
import json
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

TOKEN = os.getenv("BOT_TOKEN")

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

# ================= LINK CHECK =================
def is_link(text):
    text = text.lower()
    return ("http://" in text or "https://" in text or "t.me" in text or "www." in text)

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

# ================= GET NAME =================
def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        name = get_name(user)
        msg = await update.message.reply_text(
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
        asyncio.create_task(auto_delete(msg))

# ================= MUTE =================
async def mute_user(context, chat_id, user_id):
    until = datetime.now() + timedelta(days=1)
    await context.bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until
    )

# ================= WARN SYSTEM =================
async def handle_warn(update, context, user):
    user_id = str(user.id)
    chat_id = update.effective_chat.id

    warns = data["warns"].get(user_id, 0) + 1
    data["warns"][user_id] = warns

    name = get_name(user)

    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{user_id}")]]
    msg = await update.message.reply_text(
        f"⚠️ {name} warned\nReason: against group rules\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(msg))

    # 3 warns → mute 1 day
    if warns == 3:
        await mute_user(context, chat_id, user.id)
        m = await update.message.reply_text(f"{name} you are muted for 1 day")
        asyncio.create_task(auto_delete(m))

    # 5 warns → ban
    if warns >= 5:
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await update.message.reply_text(f"🚫 {name} banned")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user = update.message.from_user

    # ignore "admin"
    if "admin" in text:
        return

    # admin safe
    if await is_admin(update, context):
        return

    # bad word or link
    if any(word in text for word in BAD) or is_link(text):
        await update.message.delete()
        await handle_warn(update, context, user)

# ================= REMOVE WARN BUTTON =================
async def remove_warn_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_admin(update, context):
        return await query.edit_message_text("❌ Admin only")

    user_id = query.data.split("_")[1]
    data["warns"][user_id] = 0

    with open("data.json", "w") as f:
        json.dump(data, f)

    await query.edit_message_text("✅ Warn removed")

# ================= ADMIN COMMANDS =================
async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    reason = " ".join(context.args) or "No reason"

    uid = str(user.id)
    warns = data["warns"].get(uid, 0) + 1
    data["warns"][uid] = warns

    msg = await update.message.reply_text(
        f"⚠️ {get_name(user)} warned\nReason: {reason}\nTotal: {warns}"
    )
    asyncio.create_task(auto_delete(msg))

async def removewarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    data["warns"][str(user.id)] = 0

    msg = await update.message.reply_text("✅ Warn removed")
    asyncio.create_task(auto_delete(msg))

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)

    msg = await update.message.reply_text("🚫 Banned")
    asyncio.create_task(auto_delete(msg))

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)

    msg = await update.message.reply_text("✅ Unbanned")
    asyncio.create_task(auto_delete(msg))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_all))

    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    print("🔐 FINAL SECURITY BOT RUNNING 🔐")
    app.run_polling()

if __name__ == "__main__":
    main()