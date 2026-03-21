import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# ================= GET USER =================
def get_user(user):
    name = user.first_name
    username = f"@{user.username}" if user.username else name
    return name, username

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        name, username = get_user(user)
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

# ================= WARN SYSTEM =================
async def handle_warn(update, context, user):
    user_id = str(user.id)
    chat_id = update.effective_chat.id

    name, username = get_user(user)

    warns = data["warns"].get(user_id, 0) + 1
    data["warns"][user_id] = warns

    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{user_id}")]]
    msg = await update.message.reply_text(
        f"⚠️ {username} warned\n"
        f"Reason: against group rules\n"
        f"Total warns: {warns}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(msg))

    # 🔴 BAN AFTER 3 WARNS
    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await update.message.reply_text(f"🚫 {username} banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= AUTO FILTER =================
async def filter_bad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user = update.message.from_user

    # ignore admin word
    if text.strip() == "admin":
        return

    # admin safe
    if await is_admin(update, context):
        return

    # detect bad word
    if any(word in text for word in BAD):
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

# /warn (reply only)
async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to user")

    user = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "No reason"

    uid = str(user.id)
    warns = data["warns"].get(uid, 0) + 1
    data["warns"][uid] = warns

    _, username = get_user(user)

    msg = await update.message.reply_text(
        f"⚠️ {username} warned\nReason: {reason}\nTotal warns: {warns}"
    )
    asyncio.create_task(auto_delete(msg))

    if warns >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)

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
    _, username = get_user(user)

    await context.bot.ban_chat_member(update.effective_chat.id, user.id)

    msg = await update.message.reply_text(f"🚫 {username} banned")
    asyncio.create_task(auto_delete(msg))

# /unban
async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    _, username = get_user(user)

    await context.bot.unban_chat_member(update.effective_chat.id, user.id)

    msg = await update.message.reply_text(f"✅ {username} unbanned")
    asyncio.create_task(auto_delete(msg))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_bad))

    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    print("🔥 FINAL BOT RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()