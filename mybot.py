print("🚀 LEGEND V6 ULTRA LOADED")  # 🔥 CHANGE THIS EVERY TIME

import os
import json
import asyncio
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
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
    data = {"warns": {}, "filters": {}}

# ================= BAD WORDS ================
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

# ================= EXACT BAD WORD CHECK =================
def contains_bad_word(text):
    words = [w.strip(string.punctuation) for w in text.lower().split()]
    return any(word in BAD for word in words)

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
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await context.bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER SYSTEM =================
async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message.text else ""
    chat_id = update.effective_chat.id
    user = update.message.from_user
    username = get_username(user)

    # skip admins
    if await is_admin(update, context):
        return

    # ignore "admin"
    if text.lower().strip() == "admin":
        return

    # check exact bad words
    if contains_bad_word(text):
        await update.message.delete()
        await warn_user(update, context, user)
        return

    # check filters
    filters_list = data.get("filters", {}).get(str(chat_id), {})
    for keyword, content in filters_list.items():
        if keyword.lower() in text.lower():
            if "text" in content:
                await context.bot.send_message(chat_id, content["text"])
            if "file_id" in content:
                await context.bot.copy_message(chat_id, chat_id, content["file_id"])
            break

# ================= ADMIN FILTER COMMANDS =================
async def filter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    chat_id = update.effective_chat.id
    args = context.args
    if not args or not update.message.reply_to_message:
        msg = await update.message.reply_text("Usage: reply to message/video/sticker and use /filter <keyword>")
        asyncio.create_task(auto_delete(msg))
        return

    keyword = args[0].lower()
    reply = update.message.reply_to_message

    # Save filter
    if str(chat_id) not in data["filters"]:
        data["filters"][str(chat_id)] = {}
    if reply.text:
        data["filters"][str(chat_id)][keyword] = {"text": reply.text}
    else:
        file_id = None
        if reply.sticker:
            file_id = reply.sticker.file_id
        elif reply.video:
            file_id = reply.video.file_id
        elif reply.animation:
            file_id = reply.animation.file_id
        elif reply.photo:
            file_id = reply.photo[-1].file_id
        if file_id:
            data["filters"][str(chat_id)][keyword] = {"file_id": file_id}

    with open("data.json", "w") as f:
        json.dump(data, f)

    msg = await update.message.reply_text(f"✅ Filter '{keyword}' added")
    asyncio.create_task(auto_delete(msg))

async def stopfilter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        return
    keyword = args[0].lower()
    if str(chat_id) in data["filters"] and keyword in data["filters"][str(chat_id)]:
        data["filters"][str(chat_id)].pop(keyword)
        with open("data.json", "w") as f:
            json.dump(data, f)
        msg = await update.message.reply_text(f"✅ Filter '{keyword}' removed")
        asyncio.create_task(auto_delete(msg))

async def listfilters_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if str(chat_id) not in data.get("filters", {}):
        msg = await update.message.reply_text("No filters set")
        asyncio.create_task(auto_delete(msg))
        return
    filters_list = list(data["filters"][str(chat_id)].keys())
    msg = await update.message.reply_text("Filters:\n" + "\n".join(filters_list))
    asyncio.create_task(auto_delete(msg))

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
    user = None
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    elif context.args:
        mention = context.args[0].replace("@", "")
        for member in await context.bot.get_chat_administrators(update.effective_chat.id):
            if member.user.username == mention:
                user = member.user
                break
    if user:
        await warn_user(update, context, user)

async def removewarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    user = None
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    elif context.args:
        mention = context.args[0].replace("@", "")
        for member in await context.bot.get_chat_administrators(update.effective_chat.id):
            if member.user.username == mention:
                user = member.user
                break
    if user:
        data["warns"][str(user.id)] = 0
        with open("data.json", "w") as f:
            json.dump(data, f)
        msg = await update.message.reply_text(f"✅ Warn removed for {get_username(user)}")
        asyncio.create_task(auto_delete(msg))

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if user:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        msg = await update.message.reply_text(f"🚫 {get_username(user)} banned")
        asyncio.create_task(auto_delete(msg))

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if user:
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        msg = await update.message.reply_text(f"✅ {get_username(user)} unbanned")
        asyncio.create_task(auto_delete(msg))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_filters))

    # Admin commands
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("filter", filter_cmd))
    app.add_handler(CommandHandler("stopfilter", stopfilter_cmd))
    app.add_handler(CommandHandler("filters", listfilters_cmd))

    # Callback for remove warn button
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    print("🔥 LEGEND V6 ULTRA BOT RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()