print("🚀 LEGEND V3 LOADED 🚀")

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

# ================= GET NAME/USERNAME =================
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

    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await context.bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER SYSTEM =================
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Admin only")
        return
    if not update.message.reply_to_message or not context.args:
        await update.message.reply_text("Reply to a message and use: /filter <keyword>")
        return

    chat_id = str(update.effective_chat.id)
    keyword = context.args[0].lower()
    reply_msg = update.message.reply_to_message

    # detect type
    msg_type = "text"
    content_id = reply_msg.text

    if reply_msg.sticker:
        msg_type = "sticker"
        content_id = reply_msg.sticker.file_id
    elif reply_msg.animation:
        msg_type = "animation"
        content_id = reply_msg.animation.file_id
    elif reply_msg.video:
        msg_type = "video"
        content_id = reply_msg.video.file_id

    if chat_id not in filters_data:
        filters_data[chat_id] = {}

    filters_data[chat_id][keyword] = {"type": msg_type, "content": content_id}

    with open("filters.json", "w") as f:
        json.dump(filters_data, f)

    await update.message.reply_text(f"✅ Filter added for '{keyword}'")

async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Admin only")
        return
    if not context.args:
        await update.message.reply_text("Usage: /stopfilter <keyword>")
        return

    chat_id = str(update.effective_chat.id)
    keyword = context.args[0].lower()
    if chat_id in filters_data and keyword in filters_data[chat_id]:
        del filters_data[chat_id][keyword]
        with open("filters.json", "w") as f:
            json.dump(filters_data, f)
        await update.message.reply_text(f"🛑 Filter removed for '{keyword}'")
    else:
        await update.message.reply_text("❌ Filter not found")

async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in filters_data and filters_data[chat_id]:
        keywords = ", ".join(filters_data[chat_id].keys())
        await update.message.reply_text(f"📃 Filters in this group:\n{keywords}")
    else:
        await update.message.reply_text("No filters in this group.")

async def trigger_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    chat_id = str(update.effective_chat.id)
    text = update.message.text.lower()
    if chat_id not in filters_data:
        return

    for keyword, msg_info in filters_data[chat_id].items():
        if keyword in text:
            try:
                if msg_info["type"] == "text":
                    await update.message.reply_text(msg_info["content"])
                elif msg_info["type"] == "sticker":
                    await update.message.reply_sticker(msg_info["content"])
                elif msg_info["type"] == "animation":
                    await update.message.reply_animation(msg_info["content"])
                elif msg_info["type"] == "video":
                    await update.message.reply_video(msg_info["content"])
            except Exception as e:
                print("FILTER ERROR:", e)
            break

# ================= MESSAGE FILTER (BAD WORDS) =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower().strip()
    user = update.message.from_user

    # allow "admin" word
    if text == "admin":
        return

    # skip admins
    if await is_admin(update, context):
        return

    # detect bad words
    if any(word in text for word in BAD):
        try:
            await update.message.delete()
        except:
            pass
        await warn_user(update, context, user)

    # check filters
    await trigger_filter(update, context)

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
    await warn_user(update, context, user)

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

    # Welcome + Rules
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # Bad words + Filter triggers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_all))

    # Admin commands
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    # Filter system commands
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CommandHandler("filters", list_filters))

    # Remove warn button
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    print("🔥 LEGEND V3 BOT RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()