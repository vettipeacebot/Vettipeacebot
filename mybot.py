import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logging.info("🚀 LEGEND V5 ULTRA LOADED")

import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAnimation, InputMediaVideo, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from telegram.error import BadRequest

TOKEN = os.getenv("BOT_TOKEN")

# ================= DATA =================
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {"warns": {}, "filters": {}}

# ================= BAD WORDS =================
BAD = [
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
    "punda","sunni","potta","thevudiya","thayoli","oombu","nudity",
    "thevidya","ummbu","gommala","ommala","kotta","badu","ummbi",
    "thayali","aatha","otha"
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

# ================= GET USER INFO =================
def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        name = user.first_name
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
        msg = await update.message.reply_text(text)
        asyncio.create_task(auto_delete(msg))

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

    # 3 warns = ban
    if warns >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            m = await context.bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
            asyncio.create_task(auto_delete(m))
        except BadRequest:
            pass

    # Save data
    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER SYSTEM =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user

    # Skip admins
    if await is_admin(update, context):
        return

    text_lower = ""
    if update.message.text:
        text_lower = update.message.text.lower().strip()
        # skip "admin"
        if text_lower == "admin":
            return
        # bad words or links
        if any(word in text_lower for word in BAD) or "http" in text_lower or "t.me" in text_lower or "www." in text_lower:
            try:
                await update.message.delete()
            except:
                pass
            await warn_user(update, context, user)
            return

    # FILTERS
    for keyword, content in data.get("filters", {}).items():
        if keyword.lower() in (text_lower or ""):
            try:
                chat_id = update.effective_chat.id
                if content["type"] == "text":
                    await update.message.reply_text(content["value"])
                elif content["type"] == "sticker":
                    await context.bot.send_sticker(chat_id, content["file_id"])
                elif content["type"] == "video":
                    await context.bot.send_video(chat_id, content["file_id"])
                elif content["type"] == "animation":
                    await context.bot.send_animation(chat_id, content["file_id"])
                elif content["type"] == "photo":
                    await context.bot.send_photo(chat_id, content["file_id"])
            except:
                pass

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

    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    elif context.args and context.args[0].startswith("@"):
        await update.message.reply_text("Use reply to a user to warn")
        return
    else:
        return

    await warn_user(update, context, user)

async def removewarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        return

    data["warns"][str(user.id)] = 0
    msg = await update.message.reply_text(f"✅ {get_username(user)} warn removed")
    asyncio.create_task(auto_delete(msg))

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        return

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        msg = await update.message.reply_text(f"🚫 {get_username(user)} banned")
        asyncio.create_task(auto_delete(msg))
    except:
        pass

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        return

    try:
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        msg = await update.message.reply_text(f"✅ {get_username(user)} unbanned")
        asyncio.create_task(auto_delete(msg))
    except:
        pass

# ================= FILTER COMMANDS =================
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to create filter")
        return

    msg = update.message.reply_to_message
    keyword = " ".join(context.args).lower()
    if not keyword:
        await update.message.reply_text("Provide keyword after /filter")
        return

    if msg.text:
        data["filters"][keyword] = {"type": "text", "value": msg.text}
    elif msg.sticker:
        data["filters"][keyword] = {"type": "sticker", "file_id": msg.sticker.file_id}
    elif msg.video:
        data["filters"][keyword] = {"type": "video", "file_id": msg.video.file_id}
    elif msg.animation:
        data["filters"][keyword] = {"type": "animation", "file_id": msg.animation.file_id}
    elif msg.photo:
        data["filters"][keyword] = {"type": "photo", "file_id": msg.photo[-1].file_id}
    else:
        await update.message.reply_text("Unsupported type")
        return

    with open("data.json", "w") as f:
        json.dump(data, f)

    await update.message.reply_text(f"✅ Filter '{keyword}' added")

async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not context.args:
        await update.message.reply_text("Provide keyword to remove")
        return

    keyword = " ".join(context.args).lower()
    if keyword in data.get("filters", {}):
        data["filters"].pop(keyword)
        with open("data.json", "w") as f:
            json.dump(data, f)
        await update.message.reply_text(f"✅ Filter '{keyword}' removed")
    else:
        await update.message.reply_text("Keyword not found")

async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    filters_list = "\n".join(data.get("filters", {}).keys()) or "No filters"
    await update.message.reply_text(f"📄 Filters:\n{filters_list}")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Welcome new members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # Filter messages
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))

    # Admin commands
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    # Filter commands
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CommandHandler("filters", list_filters))

    # Remove warn button
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    print("🔥 LEGEND V5 ULTRA BOT RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()