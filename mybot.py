print("🚀 SECURITY BOT V8 ULTRA LOADED")  

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
BAD = set([  
    "sex","porn","xxx","nude","fuck","ass","bitch","cunt","dick",  
    "cock","pussy","slut","whore","rape","masturbate","boobs","penis",  
    "punda","sunni","potta","thevudiya","thayoli","oombu","nudity",  
    "thevidya","ummbu","gommala","ommala","kotta","badu","mairu","ummbi",  
    "thayali","aatha","otha"  
])  

PM_WORDS = ["pm","dm","private chat","private message","direct chat","direct message","inbox","add","pvrt","thaniya","pesalama","addd","added","added"]  

# ================= AUTO DELETE =================  
async def auto_delete(msg, delay=59):  
    await asyncio.sleep(delay)  
    try:  
        await msg.delete()  
    except:  
        pass  

# ================= SAFETY MESSAGE =================  
SAFETY_MSG = "🚨 DO NOT SHARE YOUR PHONE NUMBER, PHOTOS, LOCATION WITH ANYONE.\n🎯 STAY SAFE AND HAVE FUN !"  

async def safety_loop(app):  
    while True:  
        chat_ids = app.bot_data.get("all_chats", set())  
        for cid in chat_ids:  
            try:  
                msg = await app.bot.send_message(chat_id=cid, text=SAFETY_MSG)  
                asyncio.create_task(auto_delete(msg, delay=59))  
            except Exception as e:  
                print("❌ Failed to send safety message:", e)  
        await asyncio.sleep(60)  # repeat every 60 seconds  

# ================= TRACK GROUPS =================  
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    if update.effective_chat.type in ["group", "supergroup"]:  
        chat_ids = context.bot_data.get("all_chats", set())  
        chat_ids.add(update.effective_chat.id)  
        context.bot_data["all_chats"] = chat_ids  

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
async def warn_user(update, context, user, reason="against group rules"):  
    uid = str(user.id)  
    chat_id = update.effective_chat.id  

    warns = data["warns"].get(uid, 0) + 1  
    data["warns"][uid] = warns  

    btn = [[InlineKeyboardButton("Remove Warn", callback_data=f"rw_{uid}")]]  
    msg = await context.bot.send_message(  
        chat_id,  
        f"⚠️ {get_username(user)} warned\nReason: {reason}\nTotal warns: {warns}",  
        reply_markup=InlineKeyboardMarkup(btn)  
    )  
    asyncio.create_task(auto_delete(msg))  

    if warns >= 3:  
        await context.bot.ban_chat_member(chat_id, user.id)  

    with open("data.json", "w") as f:  
        json.dump(data, f)  

# ================= MESSAGE FILTER =================  
async def filter_all(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    if not update.message:  
        return  

    text = update.message.text.lower() if update.message.text else ""  
    user = update.message.from_user  

    if await is_admin(update, context):  
        return  

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

    if any(w in text for w in PM_WORDS):  
        try:  
            await update.message.delete()  
        except:  
            pass  
        return  

    words = re.findall(r"\b[a-zA-Z]+\b", text)  
    for w in words:  
        if w in BAD:  
            try:  
                await update.message.delete()  
            except:  
                pass  
            await warn_user(update, context, user)  
            return  

    chat_filters = data["filters"].get(str(update.effective_chat.id), {})  
    for key, content in chat_filters.items():  
        if key in text:  
            if content["type"] == "text":  
                await update.message.reply_text(content["value"])  
            elif content["type"] == "sticker":  
                await update.message.reply_sticker(content["value"])  
            elif content["type"] == "video":  
                await update.message.reply_video(content["value"])  
            elif content["type"] == "gif":  
                await update.message.reply_animation(content["value"])  
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
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)  
    msg = await update.message.reply_text(f"🚫 {get_username(user)} banned")  
    asyncio.create_task(auto_delete(msg))  

async def unban_cmd(update, context):  
    if not await is_admin(update, context):  
        return  
    user = await find_user(update, context)  
    if not user:  
        return await update.message.reply_text("❌ User not found")  
    await context.bot.unban_chat_member(update.effective_chat.id, user.id)  
    msg = await update.message.reply_text(f"✅ {get_username(user)} unbanned")  
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

# ================= MAIN =================  
def main():  
    app = ApplicationBuilder().token(TOKEN).build()  

    # COMMANDS  
    app.add_handler(CommandHandler("warn", warn_cmd))  
    app.add_handler(CommandHandler("removewarn", removewarn_cmd))  
    app.add_handler(CommandHandler("ban", ban_cmd))  
    app.add_handler(CommandHandler("unban", unban_cmd))  
    app.add_handler(CommandHandler("filter", add_filter))  
    app.add_handler(CommandHandler("stopfilter", stop_filter))  
    app.add_handler(CommandHandler("filters", list_filters))  

    # HANDLERS  
    app.add_handler(CallbackQueryHandler(remove_warn_btn, pattern="rw_"))  
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))  
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_all))  
    app.add_handler(MessageHandler(filters.ALL, track_chats))  

    # START SAFETY LOOP  
    app.loop.create_task(safety_loop(app))  

    print("🔥 SECURITY BOT V8 RUNNING 🔥")  
    app.run_polling()  

if __name__ == "__main__":  
    main()