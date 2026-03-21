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

 # ================= ADMIN COMMANDS WITH @USERNAME =================
async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /warn @username")
        return

    # Extract user mention
    username = context.args[0].lstrip("@")
    chat_members = await context.bot.get_chat(update.effective_chat.id)
    target_user = None
    for member in await context.bot.get_chat_administrators(update.effective_chat.id) + await update.effective_chat.get_members():
        if member.user.username and member.user.username.lower() == username.lower():
            target_user = member.user
            break

    if not target_user:
        await update.message.reply_text("❌ User not found in this group.")
        return

    await warn_user(update, context, target_user)

async def removewarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /removewarn @username")
        return

    username = context.args[0].lstrip("@")
    target_user = None
    for member in await update.effective_chat.get_members():
        if member.user.username and member.user.username.lower() == username.lower():
            target_user = member.user
            break

    if not target_user:
        await update.message.reply_text("❌ User not found.")
        return

    data["warns"][str(target_user.id)] = 0
    with open("data.json", "w") as f:
        json.dump(data, f)

    await update.message.reply_text(f"✅ Warn removed for @{username}")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /ban @username")
        return

    username = context.args[0].lstrip("@")
    target_user = None
    for member in await update.effective_chat.get_members():
        if member.user.username and member.user.username.lower() == username.lower():
            target_user = member.user
            break

    if not target_user:
        await update.message.reply_text("❌ User not found.")
        return

    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"🚫 @{username} banned")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /unban @username")
        return

    username = context.args[0].lstrip("@")
    target_user = None
    for member in await update.effective_chat.get_members():
        if member.user.username and member.user.username.lower() == username.lower():
            target_user = member.user
            break

    if not target_user:
        await update.message.reply_text("❌ User not found.")
        return

    await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"✅ @{username} unbanned")

# ================= NOTIFY ADMINS WHEN TAGGED =================
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