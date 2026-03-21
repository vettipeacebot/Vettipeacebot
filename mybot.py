print("🚀 LEGEND V6 ULTRA WEBHOOK LOADED")

import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://<project>.up.railway.app

# ================= DATA =================
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {"warns": {}}

if os.path.exists("filters.json"):
    with open("filters.json", "r") as f:
        filters_data = json.load(f)
else:
    filters_data = {}

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

# ================= GET NAME =================
def get_name(user):
    return user.first_name

def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

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

        msg = await update.message.reply_text(text)
        asyncio.create_task(auto_delete(msg))

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

    if warns >= 3:  # 3 warns → ban
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await context.bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER SYSTEM =================
async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    msg_text = update.message.text.lower().strip() if update.message.text else None

    if chat_id not in filters_data:
        return

    chat_filters = filters_data[chat_id]

    # Check text
    if msg_text and msg_text in chat_filters:
        content = chat_filters[msg_text]
        if content["type"] == "text":
            await update.message.reply_text(content["value"])
        elif content["type"] == "sticker":
            await update.message.reply_sticker(content["value"])
        elif content["type"] == "video":
            await update.message.reply_video(content["value"])
        elif content["type"] == "animation":
            await update.message.reply_animation(content["value"])

# ================= BAD WORD CHECK =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    text = update.message.text.lower() if update.message.text else ""
    if text == "admin":
        return
    if await is_admin(update, context):
        return

    # check exact word match
    words = text.split()
    for word in words:
        if word in BAD:
            try:
                await update.message.delete()
            except:
                pass
            await warn_user(update, context, user)
            return

    # check filters
    await handle_filters(update, context)

# ================= ADMIN COMMANDS =================
async def warn_cmd(update, context):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    user = update.message.reply_to_message.from_user
    await warn_user(update, context, user)

async def removewarn_cmd(update, context):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    user = update.message.reply_to_message.from_user
    data["warns"][str(user.id)] = 0
    with open("data.json", "w") as f:
        json.dump(data, f)
    msg = await update.message.reply_text("✅ Warn removed")
    asyncio.create_task(auto_delete(msg))

async def ban_cmd(update, context):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text("🚫 Banned")
    asyncio.create_task(auto_delete(msg))

async def unban_cmd(update, context):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return
    user = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text("✅ Unbanned")
    asyncio.create_task(auto_delete(msg))

# ================= FILTER COMMANDS =================
async def add_filter(update, context):
    if not await is_admin(update, context):
        return
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /filter <keyword> (reply to media/text)")
    keyword = context.args[0].lower()
    chat_id = str(update.effective_chat.id)
    if chat_id not in filters_data:
        filters_data[chat_id] = {}

    content = {}
    reply = update.message.reply_to_message
    if reply.text:
        content = {"type": "text", "value": reply.text}
    elif reply.sticker:
        content = {"type": "sticker", "value": reply.sticker.file_id}
    elif reply.video:
        content = {"type": "video", "value": reply.video.file_id}
    elif reply.animation:
        content = {"type": "animation", "value": reply.animation.file_id}
    else:
        return await update.message.reply_text("Reply to a message with text/sticker/video/animation.")

    filters_data[chat_id][keyword] = content
    with open("filters.json", "w") as f:
        json.dump(filters_data, f)
    await update.message.reply_text(f"✅ Filter saved for '{keyword}'")

async def stop_filter(update, context):
    if not await is_admin(update, context):
        return
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /stopfilter <keyword>")
    keyword = context.args[0].lower()
    chat_id = str(update.effective_chat.id)
    if chat_id in filters_data and keyword in filters_data[chat_id]:
        filters_data[chat_id].pop(keyword)
        with open("filters.json", "w") as f:
            json.dump(filters_data, f)
        await update.message.reply_text(f"✅ Filter removed for '{keyword}'")
    else:
        await update.message.reply_text("❌ Filter not found")

async def list_filters(update, context):
    if not await is_admin(update, context):
        return
    chat_id = str(update.effective_chat.id)
    if chat_id in filters_data:
        await update.message.reply_text("📜 Filters:\n" + "\n".join(filters_data[chat_id].keys()))
    else:
        await update.message.reply_text("No filters set for this chat.")

# ================= CALLBACK FOR REMOVE WARN BUTTON =================
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

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))

    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    # Filter commands
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CommandHandler("filters", list_filters))

    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    # ===== WEBHOOK =====
    port = int(os.environ.get("PORT", 8443))
    app.run_webhook(listen="0.0.0.0",
                    port=port,
                    url_path=TOKEN,
                    webhook_url=f"{WEBHOOK_URL}/{TOKEN}")

    print("🔥 LEGEND V6 ULTRA WEBHOOK RUNNING 🔥")

if __name__ == "__main__":
    main()