print("🚀 SECURITY BOT V5 ULTRA LOADED")

import os
import json
import asyncio
import re
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

# ================= BAD WORDS =================
BAD = [
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
    "punda","sunni","potta","thevudiya","thayoli","oombu","nudity",
    "thevidya","ummbu","gommala","ommala","kotta","badu","pvrt","ummbi",
    "thayali","aatha","otha"
]

PM_WORDS = ["pm","dm","private chat","private message","direct chat","direct message","inbox","add"]

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

# ================= USERNAME =================
def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

# ================= FIND USER =================
async def find_user(update, context):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user

    if context.args:
        username = context.args[0].replace("@", "")
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        for a in admins:
            if a.user.username == username:
                return a.user
    return None

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        text = (
            f"🔮 Welcome to {update.effective_chat.title}!\n"
            f"👤 Name: {user.first_name}\n"
            f"💬 Username: {get_username(user)}\n"
            f"🆔 Group ID: {update.effective_chat.id}\n\n"
            f"📜 Rules:\n"
            f"📩 Don't PM/DM others\n"
            f"🚫 Avoid bad words\n"
            f"⚠️ Follow admin instructions\n"
        )
        msg = await update.message.reply_text(text)
        asyncio.create_task(auto_delete(msg))

# ================= WARN =================
async def warn_user(update, context, user):
    uid = str(user.id)
    chat_id = update.effective_chat.id

    warns = data["warns"].get(uid, 0) + 1
    data["warns"][uid] = warns

    btn = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{uid}")]]
    msg = await context.bot.send_message(
        chat_id,
        f"⚠️ {get_username(user)} warned\nReason: against group rules\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(btn)
    )
    asyncio.create_task(auto_delete(msg))

    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER + MOD =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text.lower() if update.message.text else ""
    user = update.message.from_user

    if await is_admin(update, context):
        return

    # PM/DM delete
    if any(w in text for w in PM_WORDS):
        await update.message.delete()
        return

    # BAD WORD
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    for w in words:
        if w in BAD:
            await update.message.delete()
            await warn_user(update, context, user)
            return

    # FILTERS
    chat_filters = data["filters"].get(str(update.effective_chat.id), {})
    for key in chat_filters:
        if key in text:
            content = chat_filters[key]
            if content["type"] == "text":
                await update.message.reply_text(content["value"])
            elif content["type"] == "sticker":
                await update.message.reply_sticker(content["value"])
            elif content["type"] == "video":
                await update.message.reply_video(content["value"])
            elif content["type"] == "gif":
                await update.message.reply_animation(content["value"])
            return

    # @admin tag
    if "@admin" in text:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        tag = f"🚨 {get_username(user)} called ADMIN!\n\n"
        for a in admins:
            if a.user.username:
                tag += f"@{a.user.username} "
        msg = await update.message.reply_text(tag)
        asyncio.create_task(auto_delete(msg))

# ================= REMOVE WARN =================
async def remove_warn_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not await is_admin(update, context):
        return await q.edit_message_text("❌ Admin only")

    uid = q.data.split("_")[1]
    data["warns"][uid] = 0

    with open("data.json", "w") as f:
        json.dump(data, f)

    await q.edit_message_text("✅ Warn removed")

# ================= COMMANDS =================
async def warn_cmd(update, context):
    if not await is_admin(update, context): return
    user = await find_user(update, context)
    if user: await warn_user(update, context, user)

async def removewarn_cmd(update, context):
    if not await is_admin(update, context): return
    user = await find_user(update, context)
    if user:
        data["warns"][str(user.id)] = 0
        await update.message.reply_text("✅ Warn removed")

async def ban_cmd(update, context):
    if not await is_admin(update, context): return
    user = await find_user(update, context)
    if user:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)

async def unban_cmd(update, context):
    if not await is_admin(update, context): return
    user = await find_user(update, context)
    if user:
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)

# ================= FILTER CMDS =================
async def add_filter(update, context):
    if not await is_admin(update, context): return
    if not context.args: return

    key = context.args[0].lower()
    msg = update.message.reply_to_message
    if not msg: return

    if msg.sticker:
        ftype, val = "sticker", msg.sticker.file_id
    elif msg.video:
        ftype, val = "video", msg.video.file_id
    elif msg.animation:
        ftype, val = "gif", msg.animation.file_id
    elif msg.text:
        ftype, val = "text", msg.text
    else:
        return

    cid = str(update.effective_chat.id)
    data["filters"].setdefault(cid, {})
    data["filters"][cid][key] = {"type": ftype, "value": val}

    with open("data.json", "w") as f:
        json.dump(data, f)

    await update.message.reply_text(f"✅ Filter '{key}' added")

async def stop_filter(update, context):
    if not await is_admin(update, context): return
    if not context.args: return

    key = context.args[0].lower()
    cid = str(update.effective_chat.id)

    if key in data["filters"].get(cid, {}):
        del data["filters"][cid][key]
        await update.message.reply_text(f"🛑 Filter '{key}' removed")

async def list_filters(update, context):
    cid = str(update.effective_chat.id)
    flt = data["filters"].get(cid, {})
    if not flt:
        return await update.message.reply_text("❌ No filters")

    txt = "📂 Filters:\n" + "\n".join(f"• {k}" for k in flt)
    await update.message.reply_text(txt)

# ================= BROADCAST =================
async def all_cmd(update, context):
    if not await is_admin(update, context): return
    if not context.args: return

    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    msg = "📢 " + " ".join(context.args) + "\n\n"

    for a in admins:
        if a.user.username:
            msg += f"@{a.user.username} "

    await update.message.reply_text(msg)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CommandHandler("filters", list_filters))
    app.add_handler(CommandHandler("all", all_cmd))

    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))

    print("🔥 SECURITY BOT V5 ULTRA RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()