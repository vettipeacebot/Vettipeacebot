print("🚀 SECURITY BOT V9 PRO MAX LOADED")

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
    data = {"warns": {}, "filters": {}, "groups": {}}

# ================= CONFIG =================
ALERT_MSG = "🚨 DO NOT SHARE YOUR PHONE NUMBER, PHOTO, LOCATION WITH ANYONE.🎯 STAY SAFE HAVE FUN !"
ALERT_INTERVAL = 30
DELETE_AFTER = 28

BAD = set([
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
    "punda","sunni","potta","thevudiya","thayoli","oombu","nudity",
    "thevidya","ummbu","gommala","ommala","kotta","badu","pvrt","ummbi",
    "thayali","aatha","otha"
])

PM_WORDS = ["pm","dm","private chat","private message","direct chat","direct message","inbox","add"]

# ================= AUTO DELETE =================
async def auto_delete(msg, delay=180):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

# ================= SAVE GROUP =================
async def save_group(update):
    if update.message and update.message.chat.type in ["group", "supergroup"]:
        cid = str(update.effective_chat.id)

        if cid not in data["groups"]:
            data["groups"][cid] = {"alert": True}

            with open("data.json", "w") as f:
                json.dump(data, f)

# ================= ADMIN CHECK =================
async def is_admin(update, context):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return update.effective_user.id in [a.user.id for a in admins]
    except:
        return False

# ================= USERNAME =================
def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

# ================= FIND USER =================
async def find_user(update, context):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user

    if context.args:
        username = context.args[0].replace("@", "").lower()

        try:
            members = await context.bot.get_chat_administrators(update.effective_chat.id)
            for m in members:
                if m.user.username and m.user.username.lower() == username:
                    return m.user
        except:
            pass

    return None

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        text = (
            f"🔮 Welcome to {update.effective_chat.title}!\n"
            f"👤 Name: {user.first_name}\n"
            f"💬 Username: {get_username(user)}\n\n"
            f"📜 Rules:\n"
            f"🚫 No bad words\n"
            f"📩 No DM/PM\n"
            f"⚠️ Follow admins\n"
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
        f"⚠️ {get_username(user)} warned\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(btn)
    )

    asyncio.create_task(auto_delete(msg))

    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= FILTER =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await save_group(update)

    text = update.message.text.lower() if update.message.text else ""
    user = update.message.from_user

    if await is_admin(update, context):
        return

    # ADMIN TAG
    if "@admin" in text:
        try:
            admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            tag = f"🚨 {get_username(user)} needs ADMIN!\n\n"

            for a in admins:
                if not a.user.is_bot and a.user.username:
                    tag += f"@{a.user.username} "

            msg = await update.message.reply_text(tag)
            asyncio.create_task(auto_delete(msg))
        except:
            pass
        return

    # PM BLOCK
    if any(w in text for w in PM_WORDS):
        try:
            await update.message.delete()
        except:
            pass
        return

    # BAD WORD
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    for w in words:
        if w in BAD:
            try:
                await update.message.delete()
            except:
                pass
            await warn_user(update, context, user)
            return

# ================= ALERT SYSTEM =================
async def group_alert_task(app):
    while True:
        try:
            for cid, settings in data.get("groups", {}).items():

                if not settings.get("alert", True):
                    continue

                try:
                    msg = await app.bot.send_message(int(cid), ALERT_MSG)
                    asyncio.create_task(auto_delete(msg, DELETE_AFTER))
                except:
                    continue

            await asyncio.sleep(ALERT_INTERVAL)

        except Exception as e:
            print("Alert error:", e)
            await asyncio.sleep(ALERT_INTERVAL)

# ================= ALERT COMMAND =================
async def alert_cmd(update, context):
    if not await is_admin(update, context):
        return

    if not context.args:
        return await update.message.reply_text("Use: /alert on or /alert off")

    cid = str(update.effective_chat.id)

    if cid not in data["groups"]:
        data["groups"][cid] = {"alert": True}

    if context.args[0].lower() == "on":
        data["groups"][cid]["alert"] = True
        msg = await update.message.reply_text("✅ Alert ON")

    elif context.args[0].lower() == "off":
        data["groups"][cid]["alert"] = False
        msg = await update.message.reply_text("❌ Alert OFF")

    with open("data.json", "w") as f:
        json.dump(data, f)

    asyncio.create_task(auto_delete(msg))

# ================= BUTTON =================
async def remove_warn_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.data.split("_")[1]
    data["warns"][uid] = 0

    with open("data.json", "w") as f:
        json.dump(data, f)

    await q.edit_message_text("✅ Warn removed")

# ================= MAIN =================
async def on_startup(app):
    app.create_task(group_alert_task(app))

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("alert", alert_cmd))
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))

    print("🔥 SECURITY BOT V9 PRO MAX RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()