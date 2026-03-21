import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAnimation, InputMediaVideo, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "8443"))

# ================= DATA =================
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        data = json.load(f)
else:
    data = {"warns": {}, "filters": {}}

# ================= BAD WORDS ================
BAD = ["sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",
       "cock","pussy","slut","whore","rape","masturbate","boobs","penis",
       "punda","sunni","potta","thevudiya","thayoli","oombu","nudity",
       "thevidya","ummbu","gommala","ommala","kotta","badu","ummbi",
       "thayali","aatha","otha"]

# ================= HELPERS =================
async def auto_delete(msg, delay=180):
    await asyncio.sleep(delay)
    try: await msg.delete()
    except: pass

def get_name(user):
    return user.first_name

def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

async def is_admin(update, context):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return update.effective_user.id in [a.user.id for a in admins]
    except: return False

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
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.message.from_user
    text = (update.message.text or "").lower().strip()

    if text == "admin": return
    if await is_admin(update, context): return

    # BAD WORD CHECK
    words = text.split()
    if any(word in BAD for word in words):
        try: await update.message.delete()
        except: pass
        await warn_user(update, context, user)

    # FILTER CHECK
    chat_id = update.effective_chat.id
    filters_list = data.get("filters", {}).get(str(chat_id), {})
    for key, value in filters_list.items():
        if key.lower() in text:
            # Send saved content
            if value["type"] == "text":
                await update.message.reply_text(value["data"])
            elif value["type"] == "sticker":
                await update.message.reply_sticker(value["data"])
            elif value["type"] == "animation":
                await update.message.reply_animation(value["data"])
            elif value["type"] == "video":
                await update.message.reply_video(value["data"])
            return

# ================= REMOVE WARN BUTTON =================
async def remove_warn_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await is_admin(update, context):
        return await query.edit_message_text("❌ Admin only")
    user_id = query.data.split("_")[1]
    data["warns"][user_id] = 0
    with open("data.json", "w") as f: json.dump(data, f)
    await query.edit_message_text("✅ Warn removed")

# ================= ADMIN COMMANDS =================
async def warn_cmd(update, context):
    if not await is_admin(update, context): return
    # Reply or @username
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    elif context.args:
        username = context.args[0].lstrip("@")
        user = await context.bot.get_chat_member(update.effective_chat.id, username)
    else:
        return
    await warn_user(update, context, user)

async def removewarn_cmd(update, context):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        data["warns"][str(user.id)] = 0
        msg = await update.message.reply_text(f"✅ {get_username(user)} warn removed")
        asyncio.create_task(auto_delete(msg))

async def ban_cmd(update, context):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        msg = await update.message.reply_text(f"🚫 {get_username(user)} banned")
        asyncio.create_task(auto_delete(msg))

async def unban_cmd(update, context):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        msg = await update.message.reply_text(f"✅ {get_username(user)} unbanned")
        asyncio.create_task(auto_delete(msg))

# ================= FILTER COMMANDS =================
async def add_filter(update, context):
    if not await is_admin(update, context): return
    if not context.args or not update.message.reply_to_message: return
    key = context.args[0].lower()
    msg = update.message.reply_to_message
    chat_id = str(update.effective_chat.id)
    if chat_id not in data["filters"]: data["filters"][chat_id] = {}

    if msg.text:
        data["filters"][chat_id][key] = {"type":"text","data":msg.text}
    elif msg.sticker:
        data["filters"][chat_id][key] = {"type":"sticker","data":msg.sticker.file_id}
    elif msg.animation:
        data["filters"][chat_id][key] = {"type":"animation","data":msg.animation.file_id}
    elif msg.video:
        data["filters"][chat_id][key] = {"type":"video","data":msg.video.file_id}

    with open("data.json","w") as f: json.dump(data,f)
    await update.message.reply_text(f"✅ Filter '{key}' saved")

async def stop_filter(update, context):
    if not await is_admin(update, context): return
    if not context.args: return
    key = context.args[0].lower()
    chat_id = str(update.effective_chat.id)
    if chat_id in data["filters"] and key in data["filters"][chat_id]:
        del data["filters"][chat_id][key]
        with open("data.json","w") as f: json.dump(data,f)
        await update.message.reply_text(f"❌ Filter '{key}' removed")

async def list_filters(update, context):
    if not await is_admin(update, context): return
    chat_id = str(update.effective_chat.id)
    filters_list = data["filters"].get(chat_id,{})
    if not filters_list: await update.message.reply_text("No filters saved"); return
    keys = ", ".join(filters_list.keys())
    await update.message.reply_text(f"📋 Saved filters:\n{keys}")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # WELCOME
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    # AUTO WARN / FILTER
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))

    # ADMIN COMMANDS
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    # FILTER COMMANDS
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CommandHandler("filters", list_filters))

    # REMOVE WARN BUTTON
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    print("🚀 LEGEND V6 ULTRA LOADED")
    print("🔥 LEGEND V6 ULTRA BOT RUNNING 🔥")

    # ✅ Webhook mode for Railway
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ['RAILWAY_STATIC_URL']}/{TOKEN}"
    )

if __name__ == "__main__":
    main()