import os
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot, ChatPermissions, Message
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8443))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # your Railway webhook

bot = Bot(TOKEN)

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

# ================= UTILITIES =================
def save_data():
    with open("data.json", "w") as f:
        json.dump(data, f)

def get_name(user):
    return user.first_name

def get_username(user):
    return f"@{user.username}" if user.username else user.first_name

def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return user_id in [a.user.id for a in admins]
    except:
        return False

def auto_delete(chat_id, msg_id, delay=180):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, msg_id)
    except:
        pass

# ================= WELCOME =================
def welcome(update: Update, context: CallbackContext):
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
        msg = bot.send_message(chat_id, text)
        context.job_queue.run_once(lambda c: bot.delete_message(chat_id, msg.message_id), 180)

# ================= WARN SYSTEM =================
def warn_user(update: Update, context: CallbackContext, user):
    user_id = str(user.id)
    chat_id = update.effective_chat.id

    warns = data["warns"].get(user_id, 0) + 1
    data["warns"][user_id] = warns
    save_data()

    username = get_username(user)
    keyboard = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{user_id}")]]
    msg = bot.send_message(
        chat_id,
        f"⚠️ {username} warned\nReason: against group rules\nTotal warns: {warns}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.job_queue.run_once(lambda c: bot.delete_message(chat_id, msg.message_id), 180)

    if warns >= 3:
        bot.ban_chat_member(chat_id, user.id)
        m = bot.send_message(chat_id, f"🚫 {username} banned (3 warns)")
        context.job_queue.run_once(lambda c: bot.delete_message(chat_id, m.message_id), 180)

# ================= REMOVE WARN BUTTON =================
def remove_warn_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat.id

    if not is_admin(chat_id, query.from_user.id):
        return query.edit_message_text("❌ Admin only")

    user_id = query.data.split("_")[1]
    data["warns"][user_id] = 0
    save_data()
    query.edit_message_text("✅ Warn removed")

# ================= ADMIN COMMANDS =================
def admin_warn(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = None

    if context.args:
        username = context.args[0].replace("@", "")
        for member in bot.get_chat(chat_id).get_members():
            if member.user.username == username:
                user = member.user
                break
    elif update.message.reply_to_message:
        user = update.message.reply_to_message.from_user

    if user:
        warn_user(update, context, user)

def admin_removewarn(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = None

    if context.args:
        username = context.args[0].replace("@", "")
        for member in bot.get_chat(chat_id).get_members():
            if member.user.username == username:
                user = member.user
                break
    elif update.message.reply_to_message:
        user = update.message.reply_to_message.from_user

    if user:
        data["warns"][str(user.id)] = 0
        save_data()
        msg = bot.send_message(chat_id, f"✅ Warn removed for {get_username(user)}")
        context.job_queue.run_once(lambda c: bot.delete_message(chat_id, msg.message_id), 180)

def admin_ban(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = None

    if context.args:
        username = context.args[0].replace("@", "")
        for member in bot.get_chat(chat_id).get_members():
            if member.user.username == username:
                user = member.user
                break
    elif update.message.reply_to_message:
        user = update.message.reply_to_message.from_user

    if user:
        bot.ban_chat_member(chat_id, user.id)
        msg = bot.send_message(chat_id, f"🚫 {get_username(user)} banned")
        context.job_queue.run_once(lambda c: bot.delete_message(chat_id, msg.message_id), 180)

def admin_unban(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = None

    if context.args:
        username = context.args[0].replace("@", "")
        for member in bot.get_chat(chat_id).get_members():
            if member.user.username == username:
                user = member.user
                break
    elif update.message.reply_to_message:
        user = update.message.reply_to_message.from_user

    if user:
        bot.unban_chat_member(chat_id, user.id)
        msg = bot.send_message(chat_id, f"✅ {get_username(user)} unbanned")
        context.job_queue.run_once(lambda c: bot.delete_message(chat_id, msg.message_id), 180)

# ================= FILTER SYSTEM =================
def filter_system(update: Update, context: CallbackContext):
    msg = update.message
    if not msg:
        return
    chat_id = msg.chat.id
    text = msg.text.lower().strip() if msg.text else ""
    user = msg.from_user

    # Admin tag alert
    if "@admin" in text:
        admins = bot.get_chat_administrators(chat_id)
        mentions = [get_username(a.user) for a in admins if not a.user.is_bot]
        if mentions:
            bot.send_message(chat_id, f"⚠️ Attention Admins: {', '.join(mentions)}\nMember {get_username(user)} mentioned @admin")

    # Ignore admin
    if is_admin(chat_id, user.id):
        return

    # Exact bad word check
    words = text.split()
    for w in words:
        if w in BAD:
            bot.delete_message(chat_id, msg.message_id)
            warn_user(update, context, user)
            return

    # Filter triggers
    filters_chat = data.get("filters", {}).get(str(chat_id), {})
    for key, val in filters_chat.items():
        if key in text:
            if isinstance(val, dict) and "type" in val:
                # Sticker, video, animation
                if val["type"] == "sticker":
                    bot.send_sticker(chat_id, val["file_id"])
                elif val["type"] == "video":
                    bot.send_video(chat_id, val["file_id"])
                elif val["type"] == "animation":
                    bot.send_animation(chat_id, val["file_id"])
            else:
                bot.send_message(chat_id, val)
            return

# ================= FILTER COMMANDS =================
def add_filter(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_admin(chat_id, update.message.from_user.id):
        return

    if not context.args or not update.message.reply_to_message:
        update.message.reply_text("Usage: reply to message + /filter <keyword>")
        return

    key = context.args[0].lower()
    msg = update.message.reply_to_message

    # Save text or media
    if msg.text:
        value = msg.text
    elif msg.sticker:
        value = {"type": "sticker", "file_id": msg.sticker.file_id}
    elif msg.video:
        value = {"type": "video", "file_id": msg.video.file_id}
    elif msg.animation:
        value = {"type": "animation", "file_id": msg.animation.file_id}
    else:
        update.message.reply_text("Unsupported message type.")
        return

    if str(chat_id) not in data["filters"]:
        data["filters"][str(chat_id)] = {}

    data["filters"][str(chat_id)][key] = value
    save_data()
    update.message.reply_text(f"✅ Filter '{key}' added.")

def stop_filter(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not is_admin(chat_id, update.message.from_user.id):
        return

    if not context.args:
        update.message.reply_text("Usage: /stopfilter <keyword>")
        return

    key = context.args[0].lower()
    filters_chat = data["filters"].get(str(chat_id), {})
    if key in filters_chat:
        del filters_chat[key]
        save_data()
        update.message.reply_text(f"✅ Filter '{key}' removed.")
    else:
        update.message.reply_text(f"Filter '{key}' not found.")

def list_filters(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    filters_chat = data["filters"].get(str(chat_id), {})
    if filters_chat:
        update.message.reply_text("Filters: " + ", ".join(filters_chat.keys()))
    else:
        update.message.reply_text("No filters set.")

# ================= MAIN =================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, filter_system))

    dp.add_handler(CommandHandler("warn", admin_warn))
    dp.add_handler(CommandHandler("removewarn", admin_removewarn))
    dp.add_handler(CommandHandler("ban", admin_ban))
    dp.add_handler(CommandHandler("unban", admin_unban))
    dp.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))

    # FILTER COMMANDS
    dp.add_handler(CommandHandler("filter", add_filter))
    dp.add_handler(CommandHandler("stopfilter", stop_filter))
    dp.add_handler(CommandHandler("filters", list_filters))

    # WEBHOOK
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("🚀 LEGEND V6 ULTRA WEBHOOK LOADED")
    updater.idle()

if __name__ == "__main__":
    main()