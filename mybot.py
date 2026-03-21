import os
import json
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, filters
)

print("🚀 LEGEND V3 LOADED 🚀")

TOKEN = os.getenv("BOT_TOKEN")

# ================= DATA =================
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {
        "warns": {},
        "filters": {}
    }

# ================= BAD WORDS =================
BAD = [
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
     "punda","sunni","potta","thevudiya","thayoli","oombu","nudity",
    "thevidya","ummbu","gommala","ommala","kotta","badu","ummbi",
    "thayali","aatha","otha"
]

# ================= SAVE =================
def save():
    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= ADMIN CHECK =================
async def is_admin(update, context):
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    return update.effective_user.id in [a.user.id for a in admins]

# ================= GET NAME =================
def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

# ================= WELCOME =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        name = user.first_name
        username = f"@{user.username}" if user.username else "No username"
        
        # ✅ AUTO GROUP NAME
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

# ================= WARN =================
async def warn_user(update, context, user):
    uid = str(user.id)
    chat_id = update.effective_chat.id

    warns = data["warns"].get(uid, 0) + 1
    data["warns"][uid] = warns
    save()

    name = get_name(user)

    await context.bot.send_message(
        chat_id,
        f"⚠️ {name} warned\nReason: against group rules\nTotal warns: {warns}"
    )

    if warns >= 3:
        await context.bot.ban_chat_member(chat_id, user.id)
        await context.bot.send_message(chat_id, f"🚫 {name} banned (3 warns)")

# ================= FILTER SYSTEM =================

# ADD FILTER (ADMIN ONLY)
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admin only")

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to message")

    if not context.args:
        return await update.message.reply_text("Usage: /filter word")

    word = context.args[0].lower()
    msg = update.message.reply_to_message
    chat_id = str(update.effective_chat.id)

    if chat_id not in data["filters"]:
        data["filters"][chat_id] = {}

    # overwrite allowed
    if msg.text:
        data["filters"][chat_id][word] = {"type": "text", "content": msg.text}
    elif msg.sticker:
        data["filters"][chat_id][word] = {"type": "sticker", "content": msg.sticker.file_id}
    elif msg.animation:
        data["filters"][chat_id][word] = {"type": "gif", "content": msg.animation.file_id}
    elif msg.photo:
        data["filters"][chat_id][word] = {"type": "photo", "content": msg.photo[-1].file_id}
    else:
        return await update.message.reply_text("Unsupported type")

    save()

    await update.message.reply_text(f"✅ Filter '{word}' saved")

# REMOVE FILTER
async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not context.args:
        return await update.message.reply_text("Usage: /stop word")

    word = context.args[0].lower()
    chat_id = str(update.effective_chat.id)

    if chat_id in data["filters"] and word in data["filters"][chat_id]:
        del data["filters"][chat_id][word]
        save()
        await update.message.reply_text(f"❌ Filter '{word}' removed")
    else:
        await update.message.reply_text("Filter not found")

# ================= MAIN FILTER =================
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user = update.message.from_user
    chat_id = str(update.effective_chat.id)

    # ignore exact admin
    if text.strip() == "admin":
        return

    # skip admins
    if await is_admin(update, context):
        return

    # ================= CUSTOM FILTER REPLY =================
    if chat_id in data["filters"]:
        for word, val in data["filters"][chat_id].items():
            if word in text:
                try:
                    if val["type"] == "text":
                        await update.message.reply_text(val["content"])
                    elif val["type"] == "sticker":
                        await update.message.reply_sticker(val["content"])
                    elif val["type"] == "gif":
                        await update.message.reply_animation(val["content"])
                    elif val["type"] == "photo":
                        await update.message.reply_photo(val["content"])
                except:
                    pass
                return

    # ================= BAD WORD =================
    if any(bad in text for bad in BAD):
        try:
            await update.message.delete()
        except:
            pass

        await warn_user(update, context, user)

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
    save()

    await update.message.reply_text("✅ Warn removed")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)

    await update.message.reply_text("🚫 Banned")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)

    await update.message.reply_text("✅ Unbanned")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_all))

    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stop", stop_filter))

    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    print("🔥 LEGEND V3 BOT RUNNING 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()