async def alert_cmd(update, context):
    if not await is_admin(update, context):
        return

    cid = str(update.effective_chat.id)

    if cid not in data["groups"]:
        data["groups"][cid] = {"alert": True}

    if not context.args:
        status = data["groups"][cid]["alert"]
        msg = await update.message.reply_text(
            f"📊 Alert Status: {'ON ✅' if status else 'OFF ❌'}\nUse: /alert on or /alert off"
        )
        asyncio.create_task(auto_delete(msg))
        return

    arg = context.args[0].lower()

    if arg == "on":
        data["groups"][cid]["alert"] = True
        msg = await update.message.reply_text("✅ Alert ENABLED")

    elif arg == "off":
        data["groups"][cid]["alert"] = False
        msg = await update.message.reply_text("❌ Alert DISABLED")

    elif arg == "status":
        status = data["groups"][cid]["alert"]
        msg = await update.message.reply_text(
            f"📊 Alert Status: {'ON ✅' if status else 'OFF ❌'}"
        )

    else:
        msg = await update.message.reply_text("❌ Use: /alert on / off / status")

    with open("data.json", "w") as f:
        json.dump(data, f)

    asyncio.create_task(auto_delete(msg))