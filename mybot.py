import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # your full webhook URL

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
    "thevidya","ummbu","gommala","ommala","kotta","badu","ummbi",
    "thayali","aatha","otha"
]

AUTO_DELETE_DELAY = 180  # seconds

# ================= UTILITIES =================
def get_name(user):
    return user.first_name

def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

async def is_admin(update, context):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        return update.effective_user.id in [a.user.id for a in admins]
    except:
        return False

async def auto_delete(msg, delay=AUTO_DELETE_DELAY):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

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
    text = (update.message.text or "").lower()

    # Skip admins
    if await is_admin(update, context):
        return

    # Delete messages with PM/DM keywords automatically
    block_words = ["pm", "dm", "private message", "direct message", "chat"]
    if any(word in text for word in block_words):
        try:
            await update.message.delete()
        except:
            pass
        return

    # Admin tag alert
    if "@admin" in text:
        chat_id = update.effective_chat.id
        admins = await context.bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id != user.id:
                try:
                    await context.bot.send_message(
                        admin.user.id,
                        f"⚠️ You were tagged in {update.effective_chat.title}\n"
                        f"👤 By: {get_username(user)}\n💬 Message: {update.message.text}"
                    )
                except:
                    pass
        return

    # Exact bad word detection
    for bad in BAD:
        if f" {bad} " in f" {text} " or text.startswith(bad) or text.endswith(bad):
            await update.message.delete()
            await warn_user(update, context, user)
            return

    # Filters
    chat_id = str(update.effective_chat.id)
    chat_filters = data.get("filters", {}).get(chat_id, {})
    for keyword, value in chat_filters.items():
        if keyword.lower() in text:
            if value["type"] == "text":
                msg = await update.message.reply_text(value["content"])
            else:
                await context.bot.copy_message(chat_id, chat_id, value["message_id"])
            asyncio.create_task(auto_delete(msg) if value["type"]=="text" else None)

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
async def admin_warn(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await warn_user(update, context, user)
    elif context.args:
        # Support /warn @username
        username = context.args[0].replace("@","")
        chat_id = update.effective_chat.id
        try:
            member = await context.bot.get_chat_member(chat_id, username)
            await warn_user(update, context, member.user)
        except:
            return

async def admin_remove_warn(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        data["warns"][str(user.id)] = 0
        await update.message.reply_text(f"✅ Warn removed for {get_username(user)}")

async def admin_ban(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🚫 Banned {get_username(user)}")

async def admin_unban(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ Unbanned {get_username(user)}")

# ================= FILTER COMMANDS =================
async def add_filter(update, context):
    if not await is_admin(update, context):
        return
    if not context.args:
        return
    keyword = context.args[0].lower()
    chat_id = str(update.effective_chat.id)
    if chat_id not in data["filters"]:
        data["filters"][chat_id] = {}
    data["filters"][chat_id][keyword] = {"type": "text", "content": " ".join(context.args[1:])}
    with open("data.json", "w") as f:
        json.dump(data, f)
    await update.message.reply_text(f"✅ Filter added for {keyword}")

async def stop_filter(update, context):
    if not await is_admin(update, context):
        return
    if not context.args:
        return
    keyword = context.args[0].lower()
    chat_id = str(update.effective_chat.id)
    if chat_id in data["filters"]:
        data["filters"][chat_id].pop(keyword, None)
        with open("data.json", "w") as f:
            json.dump(data, f)
        await update.message.reply_text(f"❌ Filter removed for {keyword}")

# ================= MAIN WEBHOOK =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL, filter_all))

    app.add_handler(CommandHandler("warn", admin_warn))
    app.add_handler(CommandHandler("removewarn", admin_remove_warn))
    app.add_handler(CommandHandler("ban", admin_ban))
    app.add_handler(CommandHandler("unban", admin_unban))
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    print("🚀 LEGEND V6 ULTRA WEBHOOK LOADED")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()