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
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    return update.effective_user.id in [a.user.id for a in admins]

# ================= GET USERNAME =================
def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

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

# ================= WARN SYSTEM =================
async def handle_warn(update, context, user):
    user_id = str(user.id)
    chat_id = update.effective_chat.id

    warns = data["warns"].get(user_id, 0) + 1
    data["warns"][user_id] = warns

    name = get_username(user)

    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{user_id}")]]
    msg = await update.message.reply_text(
        f"⚠️ {name} warned\nReason: against group rules\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(msg))

    # 3 warns = ban
    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        ban_msg = await update.message.reply_text(f"🚫 {name} banned (3 warns)")
        asyncio.create_task(auto_delete(ban_msg))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user = update.message.from_user

    # ignore exact "admin"
    if text.strip() == "admin":
        return

    # admin safe (no warn, no delete)
    if await is_admin(update, context):
        return

    # detect bad words
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
async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to user")

    user = update.message.reply_to_message.from_user
    reason = " ".join(context.args) or "No reason"

    user_id = str(user.id)
    warns = data["warns"].get(user_id, 0) + 1
    data["warns"][user_id] = warns

    name = get_username(user)

    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{user_id}")]]
    msg = await update.message.reply_text(
        f"⚠️ {name} warned\nReason: {reason}\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(msg))

    if warns >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        ban_msg = await update.message.reply_text(f"🚫 {name} banned")
        asyncio.create_task(auto_delete(ban_msg))

    with open("data.json", "w") as f:
        json.dump(data, f)

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

    print("🔥 FINAL SECURITY RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()