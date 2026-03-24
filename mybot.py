print("🚀 SECURITY BOT V12 ULTRA LOADED")

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

LAST_ALERT = {}

# ================= CONFIG =================
ALERT_MSG = "⚠️📲 Do not share your phone number, photos, location with anyone.\n🍭 Stay safe have fun !"
ALERT_INTERVAL = 60
DELETE_AFTER = 58   # 58 secs

# ================= BAD WORDS =================
BAD = set([
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
    "punda","sunni","potta","thevudiya","thayoli","oombu","nudity",
    "thevidya","ummbu","gommala","ommala","kotta","badu","mairu","ummbi",
    "thayali","aatha","otha","kuthi","oluka","oolu","kuuthi","sappu","suuthu","kundi","mola"
])

PM_WORDS = ["pm","dm","private chat","private message","direct chat","direct message","inbox","add","pvrt","added","addd","adddd","thaniya"]

# ================= AUTO DELETE =================
async def auto_delete(msg, delay=DELETE_AFTER):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

# ================= SAVE GROUP =================
async def save_group(update):
    cid = str(update.effective_chat.id)
    data["groups"].setdefault(cid, {"alert": True})

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
            admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            for a in admins:
                if a.user.username and a.user.username.lower() == username:
                    return a.user
        except:
            pass

    return None

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        text = (
            f"🔱 Welcome to {update.effective_chat.title}!\n"
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
async def warn_user(update, context, user, reason="against group rules"):
    uid = str(user.id)
    chat_id = update.effective_chat.id

    warns = data["warns"].get(uid, 0) + 1
    data["warns"][uid] = warns

    btn = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{uid}")]]
    await context.bot.send_message(
        chat_id,
        f"⚠️ {get_username(user)} warned\nReason: {reason}\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(btn)
    )

    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= ALERT SYSTEM =================
async def group_alert_task(app):
    while True:
        for cid, settings in data.get("groups", {}).items():
            if not settings.get("alert", True):
                continue

            now = asyncio.get_event_loop().time()
            if cid in LAST_ALERT and now - LAST_ALERT[cid] < ALERT_INTERVAL:
                continue

            try:
                msg = await app.bot.send_message(int(cid), ALERT_MSG)
                asyncio.create_task(auto_delete(msg))
                LAST_ALERT[cid] = now
            except:
                continue

        await asyncio.sleep(5)

# ================= FILTER =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await save_group(update)

    text = update.message.text.lower() if update.message.text else ""
    user = update.message.from_user

    # ❌ REMOVE THIS (DO NOT DELETE USER MSG)
    # asyncio.create_task(auto_delete(update.message))

    # ADMIN CHECK
    if await is_admin(update, context):
        return

    # 🔥 ADMIN TAG (NO DELETE)
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

    # FILTERS
    chat_filters = data["filters"].get(str(update.effective_chat.id), {})
    for key, content in chat_filters.items():
        if key in text:
            if content["type"] == "text":
                msg = await update.message.reply_text(content["value"])
            elif content["type"] == "sticker":
                msg = await update.message.reply_sticker(content["value"])
            elif content["type"] == "video":
                msg = await update.message.reply_video(content["value"])
            elif content["type"] == "gif":
                msg = await update.message.reply_animation(content["value"])
            else:
                return

            asyncio.create_task(auto_delete(msg))
            return

# ================= BUTTON =================
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
    if not await is_admin(update, context):
        return
    user = await find_user(update, context)
    if not user:
        return await update.message.reply_text("❌ User not found")
    await warn_user(update, context, user)

async def removewarn_cmd(update, context):
    if not await is_admin(update, context):
        return
    user = await find_user(update, context)
    if not user:
        return await update.message.reply_text("❌ User not found")

    data["warns"][str(user.id)] = 0
    msg = await update.message.reply_text("✅ Warn removed")
    asyncio.create_task(auto_delete(msg))

async def ban_cmd(update, context):
    if not await is_admin(update, context):
        return

    user = await find_user(update, context)
    if not user:
        return await update.message.reply_text("❌ User not found")

    if user.id == context.bot.id:
        return await update.message.reply_text("❌ Cannot ban myself")

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        msg = await update.message.reply_text(f"🚫 {get_username(user)} banned")
        asyncio.create_task(auto_delete(msg))
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def unban_cmd(update, context):
    if not await is_admin(update, context):
        return
    user = await find_user(update, context)
    if not user:
        return await update.message.reply_text("❌ User not found")

    await context.bot.unban_chat_member(update.effective_chat.id, user.id)
    msg = await update.message.reply_text(f"✅ {get_username(user)} unbanned")

async def alert_on_cmd(update, context):
    if not await is_admin(update, context):
        return

    cid = str(update.effective_chat.id)
    data["groups"].setdefault(cid, {"alert": True})

    data["groups"][cid]["alert"] = True

    with open("data.json", "w") as f:
        json.dump(data, f)

    msg = await update.message.reply_text("✅ Alert ENABLED")
    asyncio.create_task(auto_delete(msg))


async def alert_off_cmd(update, context):
    if not await is_admin(update, context):
        return

    cid = str(update.effective_chat.id)
    data["groups"].setdefault(cid, {"alert": True})

    data["groups"][cid]["alert"] = False

    with open("data.json", "w") as f:
        json.dump(data, f)

    msg = await update.message.reply_text("❌ Alert DISABLED")
    asyncio.create_task(auto_delete(msg))

async def alert_cmd(update, context):
    if not await is_admin(update, context):
        return

    cid = str(update.effective_chat.id)
    data["groups"].setdefault(cid, {"alert": True})

    if not context.args:
        status = data["groups"][cid]["alert"]
        msg = await update.message.reply_text(f"📊 Alert: {'ON' if status else 'OFF'}")
    else:
        arg = context.args[0].lower()
        if arg == "on":
            data["groups"][cid]["alert"] = True
            msg = await update.message.reply_text("✅ Alert ON")
        elif arg == "off":
            data["groups"][cid]["alert"] = False
            msg = await update.message.reply_text("❌ Alert OFF")
        else:
            msg = await update.message.reply_text("Use: /alert on /alert off")

    with open("data.json", "w") as f:
        json.dump(data, f)

    asyncio.create_task(auto_delete(msg))

# ================= FILTER COMMANDS =================
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

    msg2 = await update.message.reply_text(f"✅ Filter '{key}' added")
    asyncio.create_task(auto_delete(msg2))

async def stop_filter(update, context):
    if not await is_admin(update, context): return
    if not context.args: return

    key = context.args[0].lower()
    cid = str(update.effective_chat.id)

    if key in data["filters"].get(cid, {}):
        del data["filters"][cid][key]

        with open("data.json", "w") as f:
            json.dump(data, f)

        msg = await update.message.reply_text(f"🛑 Filter '{key}' removed")
        asyncio.create_task(auto_delete(msg))

async def list_filters(update, context):
    cid = str(update.effective_chat.id)
    flt = data["filters"].get(cid, {})

    if not flt:
        return await update.message.reply_text("❌ No filters")

    txt = "📂 Filters:\n" + "\n".join(f"• {k}" for k in flt)
    msg = await update.message.reply_text(txt)
    asyncio.create_task(auto_delete(msg))

# ================= STARTUP =================
async def on_startup(app):
    asyncio.create_task(group_alert_task(app))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("alert", alert_cmd))
app.add_handler(CommandHandler("alerton", alert_on_cmd))
app.add_handler(CommandHandler("alertoff", alert_off_cmd))
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CommandHandler("filters", list_filters))

    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))

    print("🔥 SECURITY BOT V12 ULTRA RUNNING 🔥")

    app.post_init = on_startup

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()