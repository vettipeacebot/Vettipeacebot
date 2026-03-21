import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")

# ================= DATA =================
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {"warns": {}}

# ================= BAD WORDS =================
BAD = ["sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick","cock","pussy","slut","whore","rape","masturbate","boobs","penis",
       "punda","sunni","potta","thevudiya","thayoli","oombu","nudity","thevidya","ummbu","gommala","ommala","kotta","badu","ummbi","thayali","aatha","otha"]

# ================= UTILITIES =================
async def auto_delete(msg, delay=180):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

def get_name(user):
    return user.first_name

def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

async def is_admin(update, context):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return update.effective_user.id in [a.user.id for a in admins]
    except:
        return False

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        name = get_name(user)
        username = get_username(user)
        group_name = update.effective_chat.title
        chat_id = update.effective_chat.id

        text = (
            f"🔮 Welcome to {group_name}!\n"
            f"👤 Name: {name}\n"
            f"💬 Username: {username}\n"
            f"🆔 Group ID: {chat_id}\n\n"
            f"📜 Rules:\n"
            f"📩 Don't PM/DM others\n"
            f"🚫 Avoid bad words\n"
            f"⚠️ Follow admin instructions\n"
        )
        await update.message.reply_text(text)

# ================= WARN SYSTEM =================
async def warn_user(update, context, user):
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    warns = data["warns"].get(user_id, 0) + 1
    data["warns"][user_id] = warns

    username = get_username(user)
    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{user_id}")]]
    msg = await context.bot.send_message(
        chat_id,
        f"⚠️ {username} warned\nReason: against group rules\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(msg))

    # 3 warns = ban
    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await context.bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER BAD WORDS =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower().strip()
    user = update.message.from_user

    # allow "admin"
    if "admin" in text.lower():
        return

    if await is_admin(update, context):
        return

    # exact bad word match
    words = text.split()
    if any(word in BAD for word in words):
        try:
            await update.message.delete()
        except:
            pass
        await warn_user(update, context, user)

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
async def admin_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: /warn @username")
        return

    username = context.args[0].lstrip("@")
    target_user = None
    members = await update.effective_chat.get_administrators()
    async for member in update.effective_chat.get_members():
        if member.user.username and member.user.username.lower() == username.lower():
            target_user = member.user
            break

    if not target_user:
        await update.message.reply_text("❌ User not found")
        return

    await warn_user(update, context, target_user)

async def admin_removewarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /removewarn @username")
        return
    username = context.args[0].lstrip("@")
    target_user = None
    async for member in update.effective_chat.get_members():
        if member.user.username and member.user.username.lower() == username.lower():
            target_user = member.user
            break
    if not target_user:
        await update.message.reply_text("❌ User not found")
        return
    data["warns"][str(target_user.id)] = 0
    with open("data.json", "w") as f:
        json.dump(data, f)
    await update.message.reply_text(f"✅ Warn removed for @{username}")

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /ban @username")
        return
    username = context.args[0].lstrip("@")
    target_user = None
    async for member in update.effective_chat.get_members():
        if member.user.username and member.user.username.lower() == username.lower():
            target_user = member.user
            break
    if not target_user:
        await update.message.reply_text("❌ User not found")
        return
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"🚫 @{username} banned")

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /unban @username")
        return
    username = context.args[0].lstrip("@")
    target_user = None
    async for member in update.effective_chat.get_members():
        if member.user.username and member.user.username.lower() == username.lower():
            target_user = member.user
            break
    if not target_user:
        await update.message.reply_text("❌ User not found")
        return
    await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"✅ @{username} unbanned")

# ================= ADMIN TAG NOTIFY =================
async def admin_notify_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "@admin" in text.lower():
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        for admin in admins:
            try:
                await context.bot.send_message(
                    admin.user.id,
                    f"⚠️ You were mentioned in {update.effective_chat.title}\n"
                    f"By: @{update.message.from_user.username or update.message.from_user.first_name}\n"
                    f"Message: {update.message.text}"
                )
            except:
                continue

# ================= SETUP HANDLERS =================
def setup_handlers(app):
    # New members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    # Filter bad words
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_all))
    # Admin commands
    app.add_handler(CommandHandler("warn", admin_warn))
    app.add_handler(CommandHandler("removewarn", admin_removewarn))
    app.add_handler(CommandHandler("ban", admin_ban))
    app.add_handler(CommandHandler("unban", admin_unban))
    # Remove warn button
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))
    # Admin tag notify
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_notify_tag))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    setup_handlers(app)
    print("🚀 LEGEND V6 ULTRA BLAST MODE LOADED")
    print("🔥 LEGEND V6 ULTRA BOT RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()