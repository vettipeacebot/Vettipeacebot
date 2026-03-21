import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
)

# ================= DATA =================
if os.path.exists("data.json"):
    with open("data.json") as f:
        data = json.load(f)
else:
    data = {"warns": {}, "filters": {}}

BAD_WORDS = [
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis"
]

# ================= UTILITIES =================
async def is_admin(update, context):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return update.effective_user.id in [a.user.id for a in admins]
    except:
        return False

def get_name(user):
    return user.first_name

def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

async def auto_delete(msg, delay=180):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        name = get_name(user)
        username = get_username(user)
        group_name = update.effective_chat.title

        text = (
            f"🔮 Welcome to {group_name}!\n"
            f"👤 Name: {name}\n"
            f"💬 Username: {username}\n\n"
            f"📜 Rules:\n"
            f"📩 Don't PM/DM others\n"
            f"🚫 Avoid bad words\n"
            f"⚠️ Follow admin instructions"
        )
        await update.message.reply_text(text)

# ================= WARN SYSTEM =================
async def warn_user(update, context, user, reason="against group rules"):
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    warns = data["warns"].get(user_id, 0) + 1
    data["warns"][user_id] = warns

    username = get_username(user)
    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{user_id}")]]
    msg = await context.bot.send_message(
        chat_id,
        f"⚠️ {username} warned\nReason: {reason}\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    asyncio.create_task(auto_delete(msg))

    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await context.bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER =================
async def filter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    text = update.message.text or ""
    entities = update.message.entities or []

    # ignore admin messages
    if await is_admin(update, context):
        return

    # Allow "admin" keyword
    if text.lower().strip() == "admin":
        return

    # Bad word check (exact match)
    for word in BAD_WORDS:
        if f" {word} " in f" {text.lower()} ":
            await update.message.delete()
            await warn_user(update, context, user)
            return

    # Filters (text, sticker, GIF, video)
    chat_id = update.effective_chat.id
    chat_filters = data["filters"].get(str(chat_id), {})
    for key, value in chat_filters.items():
        if key.lower() in text.lower():
            if value.get("type") == "text":
                await update.message.reply_text(value["content"])
            else:
                await update.message.reply_sticker(value["file_id"])
            return

# ================= FILTER COMMANDS =================
async def add_filter(update, context):
    if not await is_admin(update, context):
        return
    chat_id = str(update.effective_chat.id)
    if len(context.args) < 1 or not update.message.reply_to_message:
        await update.message.reply_text("Usage: /filter <keyword> (reply to message)")
        return
    keyword = context.args[0].lower()
    reply_msg = update.message.reply_to_message
    content_type = "text"
    content_data = {"content": reply_msg.text or "", "type": "text"}
    if reply_msg.sticker:
        content_data = {"file_id": reply_msg.sticker.file_id, "type": "sticker"}
    if chat_id not in data["filters"]:
        data["filters"][chat_id] = {}
    data["filters"][chat_id][keyword] = content_data
    with open("data.json", "w") as f:
        json.dump(data, f)
    await update.message.reply_text(f"✅ Filter '{keyword}' added.")

async def stop_filter(update, context):
    if not await is_admin(update, context):
        return
    chat_id = str(update.effective_chat.id)
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /stopfilter <keyword>")
        return
    keyword = context.args[0].lower()
    if chat_id in data["filters"] and keyword in data["filters"][chat_id]:
        del data["filters"][chat_id][keyword]
        with open("data.json", "w") as f:
            json.dump(data, f)
        await update.message.reply_text(f"✅ Filter '{keyword}' removed.")

async def list_filters(update, context):
    chat_id = str(update.effective_chat.id)
    filters_list = data["filters"].get(chat_id, {})
    if not filters_list:
        await update.message.reply_text("No filters set.")
        return
    msg = "\n".join(filters_list.keys())
    await update.message.reply_text(f"Filters:\n{msg}")

# ================= REMOVE WARN BUTTON =================
async def remove_warn_btn(update, context):
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
async def admin_warn(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        await warn_user(update, context, update.message.reply_to_message.from_user)

async def admin_removewarn(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        data["warns"][str(user.id)] = 0
        with open("data.json", "w") as f:
            json.dump(data, f)
        await update.message.reply_text("✅ Warn removed")

async def admin_ban(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text("🚫 Banned")

async def admin_unban(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text("✅ Unbanned")

# ================= SETUP HANDLERS =================
def setup_handlers(app):
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_message))
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CommandHandler("filters", list_filters))
    app.add_handler(CommandHandler("warn", admin_warn))
    app.add_handler(CommandHandler("removewarn", admin_removewarn))
    app.add_handler(CommandHandler("ban", admin_ban))
    app.add_handler(CommandHandler("unban", admin_unban))
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))