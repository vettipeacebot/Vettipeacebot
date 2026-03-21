print("🚀 SECURITY BOT V3 LOADED")  # 🔥 CHANGE THIS EVERY TIME

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
    data = {"warns": {}, "filters": {}}

# ================= BAD WORDS ================
BAD = [
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
    "punda","sunni","potta","thevudiya","thayoli","oombu","nudity",
    "thevidya","ummbu","gommala","ommala","kotta","badu","pvrt","ummbi",
    "thayali","aatha","otha"
]

PM_WORDS = ["pm","dm","private chat","private message","direct chat","direct message","inbox"]

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
        name = user.first_name
        username = f"@{user.username}" if user.username else "No username"
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

    # 3 WARNS = BAN
    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await context.bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER HANDLER =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text.lower() if update.message.text else ""
    user = update.message.from_user

    # Skip admins
    if await is_admin(update, context):
        return

    # PM/DM words auto delete
    if any(word in text for word in PM_WORDS):
        try:
            await update.message.delete()
        except:
            pass
        return

    # Bad word detection (exact word match)
    words = text.split()
    for w in words:
        if w.lower() in BAD:
            try:
                await update.message.delete()
            except:
                pass
            await warn_user(update, context, user)
            return

    # Filter system
    chat_filters = data.get("filters", {}).get(str(update.effective_chat.id), {})
    for key, content in chat_filters.items():
        if key.lower() in text:
            # Send saved sticker/text/video
            if content["type"] == "text":
                await update.message.reply_text(content["value"])
            elif content["type"] == "sticker":
                await update.message.reply_sticker(content["value"])
            elif content["type"] == "video":
                await update.message.reply_video(content["value"])
            return

    # @admin mentions notify all admins
    if "@admin" in text:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        for a in admins:
            try:
                await context.bot.send_message(a.user.id, f"⚠️ You were tagged by {get_username(user)} in {update.effective_chat.title}")
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
    # Reply or @username
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await warn_user(update, context, user)
    elif context.args:
        username = context.args[0].lstrip("@")
        for m in await update.effective_chat.get_members():
            if m.user.username == username:
                await warn_user(update, context, m.user)
                break

async def removewarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    elif context.args:
        username = context.args[0].lstrip("@")
        for m in await update.effective_chat.get_members():
            if m.user.username == username:
                user = m.user
                break
    else:
        return
    data["warns"][str(user.id)] = 0
    with open("data.json", "w") as f:
        json.dump(data, f)
    msg = await update.message.reply_text("✅ Warn removed")
    asyncio.create_task(auto_delete(msg))

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    elif context.args:
        username = context.args[0].lstrip("@")
        for m in await update.effective_chat.get_members():
            if m.user.username == username:
                user = m.user
                break
    else:
        return
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text(f"🚫 {get_username(user)} banned")
    asyncio.create_task(auto_delete(msg))

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    elif context.args:
        username = context.args[0].lstrip("@")
        for m in await update.effective_chat.get_members():
            if m.user.username == username:
                user = m.user
                break
    else:
        return
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text(f"✅ {get_username(user)} unbanned")
    asyncio.create_task(auto_delete(msg))

# ================= FILTER COMMANDS =================
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        return
    keyword = context.args[0].lower()
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        ftype = "text"
        fval = msg.text or msg.sticker.file_id or msg.video.file_id
        if msg.sticker:
            ftype = "sticker"
        elif msg.video:
            ftype = "video"
        elif msg.text:
            ftype = "text"
        chat_id = str(update.effective_chat.id)
        if chat_id not in data["filters"]:
            data["filters"][chat_id] = {}
        data["filters"][chat_id][keyword] = {"type": ftype, "value": fval}
        with open("data.json", "w") as f:
            json.dump(data, f)
        await update.message.reply_text(f"✅ Filter '{keyword}' added")

async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        return
    keyword = context.args[0].lower()
    chat_id = str(update.effective_chat.id)
    if chat_id in data["filters"] and keyword in data["filters"][chat_id]:
        del data["filters"][chat_id][keyword]
        with open("data.json", "w") as f:
            json.dump(data, f)
        await update.message.reply_text(f"🛑 Filter '{keyword}' removed")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Admin commands
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))

    # Callback remove warn
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    # General message handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))

    print("🔥 SECURITY BOT V3 RUNNING 🔥")
    app.run_polling()  # Change to run_webhook() if you deploy on webhook

if __name__ == "__main__":
    main()