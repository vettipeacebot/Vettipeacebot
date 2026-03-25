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

    # ✅ FIX missing keys
    data.setdefault("lang", {})
    data.setdefault("warns", {})
    data.setdefault("filters", {})
    data.setdefault("groups", {})
else:
    data = {
        "lang": {},
        "warns": {},
        "filters": {},
        "groups": {}
    }

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
async def save_group(update, context=None):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    cid = str(update.effective_chat.id)
    title = update.effective_chat.title

    data["groups"].setdefault(cid, {"alert": True, "title": title})
    data["groups"][cid]["title"] = title

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


# ================= START (PM PANEL) =================
TEXT = {
    "en": {
        "start": "🔱 Hello!\n\nναηηαкαм ∂α мαρℓα is the most complete Bot to help you manage your groups easily and safely!\n\n🫴 Add me in a Supergroup and promote me as Admin to let me get in action!\n\n❗WHICH ARE THE COMMANDS? ❗\nPress /help to see all the commands!",
        "manage": "⚙️ Manage group settings",
        "support": "Support 📩",
        "info": "Information 🤖",
        "lang": "🇮🇳 Languages 🇮🇳",
        "add": "➕ Add me to a group ➕",
        "settings": "Manage group Settings\n\n👉🏻 Select the group whose settings you want to change.",
        "botsupport": "🛠 Bot Support",
        "commands": "📖 Commands",
        "privacy": "💡 Privacy Policy",
        "back": "⬅️ Back"
    },
    "ta": {
        "start": "🔱 வணக்கம்!\n\nவணக்கம்டா மாப்பிள்ளை Bot உங்கள் குழுக்களை பாதுகாப்பாக நிர்வகிக்க உதவும்!\n\n🫴 என்னை குழுவில் Admin ஆக்குங்கள்!\n\n❗கட்டளைகளை பார்க்க /help அழுத்துங்கள்!",
        "manage": "⚙️ குழு அமைப்புகள்",
        "support": "📩 ஆதரவு",
        "botsupport": "🛠 உதவி",
        "info": "🤖 தகவல்",
        "lang": "🌐 மொழிகள்",
        "add": "➕ குழுவில் சேர்க்க",
        "settings": "⚙️ குழு அமைப்புகள்\n\n👉 மாற்ற வேண்டிய குழுவை தேர்வு செய்யவும்",
        "back": "🔙 திரும்ப",
        "commands": "📖 கட்டளைகள்",
        "privacy": "💡 தனியுரிமை"
    }
}

def get_lang(uid):
    return data["lang"].get(str(uid), "en")

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    uid = str(update.effective_user.id)
    lang = get_lang(uid)
    t = TEXT[lang]

    buttons = [
    [InlineKeyboardButton(t["add"], url=f"https://t.me/{context.bot.username}?startgroup=true")],
    [InlineKeyboardButton(t["manage"], callback_data="manage")],
    [InlineKeyboardButton(t["support"], callback_data="support")],
    [InlineKeyboardButton(t["info"], callback_data="info")],
    [InlineKeyboardButton(t["lang"], callback_data="lang")]
]

    await update.message.reply_text(t["start"], reply_markup=InlineKeyboardMarkup(buttons))

# ================= LANGUAGE =================
async def language_menu(update, context):
    q = update.callback_query
    await q.answer()

    buttons = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇮🇳 Tamil", callback_data="lang_ta")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]

    await q.edit_message_text("🌐 Select Language", reply_markup=InlineKeyboardMarkup(buttons))

async def set_language(update, context, lang_code):
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)
    data["lang"][uid] = lang_code

    with open("data.json", "w") as f:
        json.dump(data, f)

    await back_menu(update, context)

# ================= MANAGE =================
async def manage(update, context):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    buttons = []

    for gid, info in data["groups"].items():
        try:
            admins = await context.bot.get_chat_administrators(int(gid))
            if uid in [a.user.id for a in admins]:
                buttons.append([InlineKeyboardButton(info["title"], callback_data=f"grp_{gid}")])
        except:
            continue

    if not buttons:
        return await q.edit_message_text("⚠️ No groups found!")

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back")])

    await q.edit_message_text("Select your group:", reply_markup=InlineKeyboardMarkup(buttons))

# ================= SETTINGS COMMAND =================
async def settings_cmd(update, context):
    if update.effective_chat.type != "private":
        return

    uid = str(update.effective_user.id)
    lang = get_lang(uid)
    t = TEXT[lang]

    buttons = []
    for gid, info in data["groups"].items():
        try:
            admins = await context.bot.get_chat_administrators(int(gid))
            if int(uid) in [a.user.id for a in admins]:
                buttons.append([InlineKeyboardButton(info["title"], callback_data=f"grp_{gid}")])
        except:
            continue

    await update.message.reply_text(t["settings"], reply_markup=InlineKeyboardMarkup(buttons))

# ================= SUPPORT (HTML SAFE) =================
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)
    lang = get_lang(uid)
    t = TEXT[lang]

    # HTML text for English and Tamil
    if lang == "ta":
        text = (
            "📩 <b>ஆதரவு மையம்</b>\n"
            "_உதவி மற்றும் தொடர்புக்கு_\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🎯 <b>Developer</b>\n"
            "• நேரடி தொடர்புக்கு கீழே உள்ள பட்டன்களை பயன்படுத்தவும்\n"
            "━━━━━━━━━━━━━━━\n\n"
            "⚠️ <b>கவனம்</b>\n"
            "• குழு பிரச்சனைகள் (ban, mute போன்றவை) ஆதரவு வழங்கப்படாது\n"
            "• தயவுசெய்து குழு Admin-ஐ தொடர்பு கொள்ளவும்\n\n"
            "💡 தேவையெனில் Developer-ஐ தொடர்பு கொள்ளுங்கள்"
        )
    else:
        text = (
            "📩 <b>Support Center</b>\n"
            "_Get help & contact developer_\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🎯 <b>Developer</b>\n"
            "• Use the buttons below to contact directly\n"
            "━━━━━━━━━━━━━━━\n\n"
            "⚠️ <b>Important Notice</b>\n"
            "• We do NOT support group issues (ban, mute, etc.)\n"
            "• Contact your group admins\n\n"
            "💡 Reach out to developer if needed"
        )

    # Buttons
    buttons = [
        [InlineKeyboardButton("📲 Telegram", url="https://t.me/vettipeace"),
         InlineKeyboardButton("📳 Instagram", url="https://instagram.com/vettipeace")],
        [InlineKeyboardButton("📧 Email", callback_data="email_support"),
         InlineKeyboardButton(t["back"], callback_data="back")]
    ]

    await q.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"  # Changed from MarkdownV2
    )

# ================= EMAIL SUPPORT CALLBACK =================
async def email_support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    text = (
        "📧 To contact the developer via email, use:\n"
        "<b>mohamedaflal1999786@gmail.com</b>\n\n"
        "You can copy and paste this in your email client."
    )

    await q.edit_message_text(
        text=text,
        parse_mode="HTML"
    )

# ================= INFO (PREMIUM UI) =================
async def info(update, context):
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)
    lang = get_lang(uid)
    t = TEXT[lang]

    if lang == "ta":
        text = (
            "🔱 **ναηηαкαм ∂α мαρℓα**\n"
            "_சிறந்த குழு மேலாண்மை Bot_\n\n"

            "━━━━━━━━━━━━━━━\n"
            "🤖 **Bot தகவல்**\n"
            "• பதிப்பு : V12\n"
            "• ஆரம்பம் : 24 மார்ச் 2026\n"
            "• நிலை : செயல்பாட்டில்\n"
            "━━━━━━━━━━━━━━━\n\n"

            "👑 **Bot நிர்வாகிகள்**\n"
            "• @vettipeace\n"
            "• @tammy10117\n\n"

            "⚠️ **முக்கிய அறிவிப்பு**\n"
            "குழு பிரச்சனைகளுக்கு உதவி வழங்கப்படாது.\n"
            "Admin-ஐ தொடர்பு கொள்ளவும்.\n\n"

            "💖 **ஆதரவாளர்கள்**\n"
            "• நிதியுதவி செய்த அனைவருக்கும் நன்றி ❤️\n"
            "• பிழைகள் தெரிவித்தவர்களுக்கு நன்றி\n"
            "• இந்த Bot பயன்படுத்தும் குழுக்களுக்கு நன்றி\n\n"

            "🚀 எங்கள் Bot தொடர்ந்து மேம்படுத்தப்படுகிறது!"
        )
    else:
        text = (
            "🔱 **ναηηαкαм ∂α мαρℓα**\n"
            "_Smart Group Management Bot_\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🤖 **Bot Information**\n"
            "• Version : V12\n"
            "• Online Since : 24 March 2026\n"
            "• Status : Active & Updated\n"
            "━━━━━━━━━━━━━━━\n\n"
            "👑 **Bot Admins**\n"
            "• @vettipeace\n"
            "• @tammy10117\n\n"
            "⚠️ **Important Notice**\n"
            "Bot staff cannot assist in group-related issues.\n\n"
            "💖 **Supporters**\n"
            "• Thanks to all donors ❤️\n"
            "• Thanks for suggestions\n"
            "🚀 We are improving!"
        )

    buttons = [
        [InlineKeyboardButton(t["botsupport"], callback_data="botsupport")],
        [InlineKeyboardButton(t["commands"], callback_data="help")],
        [InlineKeyboardButton(t["privacy"], url="https://t.me/vettipeace")],
        [InlineKeyboardButton(t["back"], callback_data="back")]
    ]

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

# ================= BOT SUPPORT =================
async def bot_support(update, context):
    q = update.callback_query
    await q.answer()

    lang = get_lang(str(q.from_user.id))
    t = TEXT[lang]

    if lang == "ta":
        text = (
            "<b>⚠️ இந்த Bot குழு தொடர்பான (ban, mute போன்ற) பிரச்சனைகளுக்கு உதவி வழங்காது.</b>\n\n"
            "👉 தயவுசெய்து குழு Admin-ஐ தொடர்பு கொள்ளவும்."
        )
    else:
        text = (
            "<b>⚠️ We do NOT provide support for ban, mute or other group issues.</b>\n\n"
            "👉 Contact your group admins."
        )

    buttons = [
        [InlineKeyboardButton(t["back"], callback_data="back")]
    ]

    await q.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

# ================= HELP (PREMIUM UI) =================
async def help_cmd(update, context):
    lang = get_lang(str(update.effective_user.id))

    if lang == "ta":
        text = (
            "📜 **Bot கட்டளைகள்**\n\n"

            "👮 Admin Commands\n"
            "• /warn – எச்சரிக்கை\n"
            "• /ban – தடை\n"
            "• /unban – தடை நீக்கு\n\n"

            "🧠 Filter System\n"
            "• /filter – auto reply\n"
            "• /filters – பட்டியல்\n\n"

            "🔔 Alert System\n"
            "• /alert on/off\n\n"

            "⚙️ Features\n"
            "• Bad word block\n"
            "• PM block\n"
        )
    else:
        text = (
            "📜 **Bot Commands Guide**\n"
            "_Manage your group like a pro_\n\n"

            "━━━━━━━━━━━━━━━\n"
            "👮 **Admin Commands**\n"
            "• /warn – Warn a user\n"
            "• /removewarn – Reset warns\n"
            "• /ban – Ban user\n"
            "• /unban – Unban user\n\n"

            "━━━━━━━━━━━━━━━\n"
            "🧠 **Filter System**\n"
            "• /filter – Add auto reply\n"
            "• /stopfilter – Remove filter\n"
            "• /filters – List filters\n\n"

            "━━━━━━━━━━━━━━━\n"
            "🔔 **Alert System**\n"
            "• /alert – Check status\n"
            "• /alert on – Enable alerts\n"
            "• /alert off – Disable alerts\n\n"

            "━━━━━━━━━━━━━━━\n"
            "⚙️ **Other Features**\n"
            "• Auto delete messages\n"
            "• Bad word protection\n"
            "• PM/DM block system\n"
            "• Admin tag system (@admin)\n\n"

            "🚀 _More features coming soon..._"
        )

    buttons = [
        [InlineKeyboardButton(TEXT[lang]["botsupport"], callback_data="botsupport")],
        [InlineKeyboardButton(TEXT[lang]["back"], callback_data="back")]
    ]

    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )

# ================= CALLBACK =================
async def menu(update, context):
    q = update.callback_query
    data_cb = q.data

    if data_cb == "manage":
        await manage(update, context)
    elif data_cb == "support":
        await support(update, context)
    elif data_cb == "botsupport":
        await bot_support(update, context)
    elif data_cb == "info":
        await info(update, context)
    elif data_cb == "lang":
        await language_menu(update, context)
    elif data_cb.startswith("lang_"):
        await set_language(update, context, data_cb.split("_")[1])
    elif data_cb == "help":
        await help_cmd(update, context)

# ================= BACK =================
async def back_menu(update, context):
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)
    lang = get_lang(uid)
    t = TEXT[lang]

    buttons = [
        [InlineKeyboardButton(t["add"], url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton(t["manage"], callback_data="manage")],
        [InlineKeyboardButton(t["support"], callback_data="support")],
        [InlineKeyboardButton(t["info"], callback_data="info")],
        [InlineKeyboardButton(t["lang"], callback_data="lang")]
    ]

    await q.edit_message_text(t["start"], reply_markup=InlineKeyboardMarkup(buttons))

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

    # 🚫 VERY IMPORTANT FIX
    if update.effective_chat.type == "private":
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

    # 🔥 PM COMMANDS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))

    # 🔥 CALLBACK HANDLERS (VERY IMPORTANT ORDER)

    # ----------------------
    # Dedicated Callback Handlers
    # ----------------------

    # Back Button
    app.add_handler(CallbackQueryHandler(back_menu, pattern="^back$"))

    # Remove Warn Button
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="^rw_"))

    # Bot Support (dedicated)
    app.add_handler(CallbackQueryHandler(bot_support, pattern="^botsupport$"))

    # Email Support (dedicated)
    app.add_handler(CallbackQueryHandler(email_support_callback, pattern="^email_support$"))

    # Menu Buttons (manage, support, info, lang, help, lang_xx, grp_xxx)
    app.add_handler(CallbackQueryHandler(menu, pattern="^(manage|support|info|lang|help|lang_.*|grp_.*)$"))

    # 🔥 ALERT COMMANDS
    app.add_handler(CommandHandler("alert", alert_cmd))
    app.add_handler(CommandHandler("alerton", alert_on_cmd))
    app.add_handler(CommandHandler("alertoff", alert_off_cmd))

    # 🔥 ADMIN COMMANDS
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    # 🔥 FILTER COMMANDS
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("stopfilter", stop_filter))
    app.add_handler(CommandHandler("filters", list_filters))

    # 🔥 EVENTS
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))

    # 🔥 SAVE GROUP DATA (KEEP LAST)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, save_group))

    print("🔥 SECURITY BOT V12 ULTRA RUNNING 🔥")

    app.post_init = on_startup

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()