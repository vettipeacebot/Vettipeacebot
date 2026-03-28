print("🚀 SECURITY BOT V12 ULTRA LOADED")

import os
import json
import asyncio
import re
import feedparser  
import time
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
    data.setdefault("news", {})
    data.setdefault("posted_news", {})
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

PM_WORDS = ["pm","dm","private chat","private message","direct chat","direct message","inbox","add","pvrt","added","addd","adddd","thaniya"]

NEWS_FEEDS = [
    "https://www.dinamalar.com/rss.asp",
    "https://www.indiatoday.in/rss/1206578"
]
NEWS_INTERVAL = 3600
BREAKING_INTERVAL = 1800
NEWS_DELETE = 86400

# ================= AUTO DELETE =================
async def auto_delete(msg, delay=DELETE_AFTER, NEWS_DELETE=True):
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
        "back": "🔙 Back"
    },
    "ta": {
        "start": "🔱 வணக்கம்!\n\nவணக்கம்டா மாப்பிள்ளை Bot உங்கள் குழுக்களை பாதுகாப்பாக நிர்வகிக்க உதவும்!\n\n🫴 என்னை குழுவில் Admin ஆக்குங்கள்!\n\n❗கட்டளைகளை பார்க்க /help அழுத்துங்கள்!",
        "manage": "⚙️ குழு அமைப்புகள்",
        "support": "📩 ஆதரவு",
        "botsupport": "🛠 உதவி",
        "info": "🤖 தகவல்",
        "lang": "🇮🇳 மொழிகள்",
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

            "🧠 Filter System\n"
            "• /filter – auto reply\n"
            "• /filters – பட்டியல்\n\n"

            "🔔 Alert System\n"
            "• /alert on/off\n\n"

            "⚙️ Features\n"
            "• PM block\n"
        )
    else:
        text = (
            "📜 **Bot Commands Guide**\n"
            "_Manage your group like a pro_\n\n"
            "🧠 **Filter System**\n"
            "• /filter – Add auto reply\n"
            "• /stopfilter – Remove filter\n"
            "• /filters – List filters\n\n"

            "🔔 **Alert System**\n"
            "• /alert – Check status\n"
            "• /alert on – Enable alerts\n"
            "• /alert off – Disable alerts\n\n"
            "⚙️ **Other Features**\n"
            "• Auto delete messages\n"
            "• PM/DM block system\n"

            "🚀 _More features coming soon..._"
        )

    # ✅ Only keep the Back button
    buttons = [
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

# ================= NEWS SYSTEM =================    

# 🔥 CLEAN HTML
def clean_html(raw_html):
    return re.sub('<.*?>', '', raw_html)

# 🔥 EXTRACT IMAGE
def extract_image(entry):
    if "media_content" in entry:
        return entry.media_content[0]["url"]

    if "summary" in entry:
        match = re.search(r'<img.*?src="(.*?)"', entry.summary)
        if match:
            return match.group(1)

    return None


# ================= GET NEWS =================
async def get_news():
    for url in NEWS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            news_id = entry.get("id", entry.link)

            # ❌ skip already posted
            if news_id in data["posted_news"]:
                continue

            # ❌ skip old news (24h)
            if hasattr(entry, "published_parsed"):
                published = time.mktime(entry.published_parsed)
                if time.time() - published > 86400:
                    continue

            return entry

    return None


# ================= SEND NEWS =================
async def send_news(app, entry, breaking=False):
    news_id = entry.get("id", entry.link)

    title = entry.title
    summary_raw = entry.get("summary", "")

    # ✅ clean + limit summary
    summary = clean_html(summary_raw)[:300]

    image = extract_image(entry)

    if breaking:
        caption = f"""🚨 <b>BREAKING NEWS</b>

📰 <b>{title}</b>

{summary}...
"""
    else:
        caption = f"""📰 <b>NEWS UPDATE</b>

<b>{title}</b>

{summary}...
"""

    for cid in data.get("groups", {}):
        if not data["news"].get(cid, True):
            continue

        try:
            if image:
                msg = await app.bot.send_photo(
                    chat_id=int(cid),
                    photo=image,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⚡ Instant View", url=entry.link)]
                    ])
                )
            else:
                msg = await app.bot.send_message(
                    chat_id=int(cid),
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⚡ Instant View", url=entry.link)]
                    ])
                )

            # 🔥 Auto delete after NEWS_DELETE seconds (default 86400 = 24h)
            asyncio.create_task(auto_delete(msg, delay=NEWS_DELETE))

        except Exception as e:
            print("News error:", e)

    # ✅ mark as posted
    data["posted_news"][news_id] = True

    with open("data.json", "w") as f:
        json.dump(data, f)

# ================= BREAKING NEWS TASK =================
async def breaking_news_task(app):
    while True:
        entry = await get_news()

        if entry:
            await send_news(app, entry, breaking=True)  # 🚨 breaking style

        await asyncio.sleep(BREAKING_INTERVAL)


# ================= HOURLY NEWS TASK =================
async def hourly_news_task(app):
    while True:
        for _ in range(2):  # 🔥 send 2 news every hour
            entry = await get_news()

            if entry:
                await send_news(app, entry, breaking=False)  # 📰 normal style

        await asyncio.sleep(NEWS_INTERVAL)

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

    # ADMIN CHECK
    if await is_admin(update, context):
        return

    # PM BLOCK
    if any(w in text for w in PM_WORDS):
        try:
            await update.message.delete()
        except:
            pass
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

# ================= COMMANDS =================
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

# ================= NEWS COMMAND =================
async def news_cmd(update, context):
    if not await is_admin(update, context):
        return

    cid = str(update.effective_chat.id)
    data["news"].setdefault(cid, True)

    if not context.args:
        status = "ON" if data["news"][cid] else "OFF"
        msg = await update.message.reply_text(f"📢 News: {status}")
    else:
        arg = context.args[0].lower()
        if arg == "on":
            data["news"][cid] = True
            msg = await update.message.reply_text("✅ News ENABLED")
        elif arg == "off":
            data["news"][cid] = False
            msg = await update.message.reply_text("❌ News DISABLED")
        else:
            msg = await update.message.reply_text("Use: /news on | /news off")

    # Save changes
    with open("data.json", "w") as f:
        json.dump(data, f)

    # Auto-delete message
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

async def on_startup(app):
    # Start alert task
    asyncio.create_task(group_alert_task(app))
    
    # Start breaking news task
    asyncio.create_task(breaking_news_task(app))
    
    # Start hourly news task
    asyncio.create_task(hourly_news_task(app))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # 🔥 PM COMMANDS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))

    # 🔥 CALLBACK HANDLERS (VERY IMPORTANT ORDER)
    app.add_handler(CallbackQueryHandler(back_menu, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(bot_support, pattern="^botsupport$"))
    app.add_handler(CallbackQueryHandler(email_support_callback, pattern="^email_support$"))
    app.add_handler(CallbackQueryHandler(menu, pattern="^(manage|support|info|lang|help|lang_.*|grp_.*)$"))

    # 🔥 ALERT COMMANDS
    app.add_handler(CommandHandler("alert", alert_cmd))
    app.add_handler(CommandHandler("alerton", alert_on_cmd))
    app.add_handler(CommandHandler("alertoff", alert_off_cmd))

    # 🔥 NEWS COMMAND
    app.add_handler(CommandHandler("news", news_cmd))

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