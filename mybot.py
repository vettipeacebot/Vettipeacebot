print("🚀 LEGEND V4 ULTRA LOADED")  # 🔥 CHANGE THIS EVERY TIME

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
            f"⚠️ Follow admin instructions"
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

    # 3 warns → BAN
    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        m = await context.bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
        asyncio.create_task(auto_delete(m))

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER SYSTEM =================
async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.lower().strip() if update.message.text else ""
    user = update.message.from_user

    # skip admins
    if await is_admin(update, context):
        return

    # skip 'admin' word
    if text == "admin":
        return

    # detect bad words
    if any(word in text for word in BAD):
        try:
            await update.message.delete()
        except:
            pass
        await warn_user(update, context, user)
        return

    # check filters
    for keyword, fdata in data.get("filters", {}).items():
        if keyword in text:
            chat_id = update.effective_chat.id
            ftype = fdata["type"]
            file_id = fdata["file_id"]
            if ftype == "text":
                msg = await context.bot.send_message(chat_id, file_id)
            else:  # sticker/video/animation
                send_method = getattr(context.bot, f"send_{ftype}")
                msg = await send_method(chat_id, file_id)
            asyncio.create_task(auto_delete(msg))
            break

# ================= FILTER COMMANDS =================
async def filter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message or not context.args:
        return await update.message.reply_text("Reply to a message and use /filter <keyword>")

    keyword = context.args[0].lower()
    msg = update.message.reply_to_message

    if msg.text:
        ftype = "text"
        fid = msg.text
    elif msg.sticker:
        ftype = "sticker"
        fid = msg.sticker.file_id
    elif msg.video:
        ftype = "video"
        fid = msg.video.file_id
    elif msg.animation:
        ftype = "animation"
        fid = msg.animation.file_id
    else:
        return

    data["filters"][keyword] = {"type": ftype, "file_id": fid}
    with open("data.json", "w") as f:
        json.dump(data, f)
    await update.message.reply_text(f"✅ Filter '{keyword}' added.")

async def stopfilter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not context.args:
        return await update.message.reply_text("Use /stopfilter <keyword>")

    keyword = context.args[0].lower()
    if keyword in data.get("filters", {}):
        del data["filters"][keyword]
        with open("data.json", "w") as f:
            json.dump(data, f)
        await update.message.reply_text(f"❌ Filter '{keyword}' removed.")
    else:
        await update.message.reply_text(f"No filter found for '{keyword}'.")

async def listfilters_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data.get("filters"):
        return await update.message.reply_text("No filters added yet.")
    filters_list = "\n".join(data["filters"].keys())
    await update.message.reply_text(f"📝 Active filters:\n{filters_list}")

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
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    user = update.message.reply_to_message.from_user
    await warn_user(update, context, user)

async def removewarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    user = update.message.reply_to_message.from_user
    data["warns"][str(user.id)] = 0
    msg = await update.message.reply_text("✅ Warn removed")
    asyncio.create_task(auto_delete(msg))

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text("🚫 Banned")
    asyncio.create_task(auto_delete(msg))

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    user = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text("✅ Unbanned")
    asyncio.create_task(auto_delete(msg))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Welcome
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # Bad words + filters
    app.add_handler(MessageHandler(filters.ALL, handle_filters))

    # Admin commands
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    # Filter commands
    app.add_handler(CommandHandler("filter", filter_cmd))
    app.add_handler(CommandHandler("stopfilter", stopfilter_cmd))
    app.add_handler(CommandHandler("filters", listfilters_cmd))

    # Remove warn button
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    print("🔥 LEGEND V4 ULTRA BOT RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()