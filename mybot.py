import os
from telegram.ext import ApplicationBuilder
from mybot_logic import setup_handlers

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Your Railway project URL
PORT = int(os.environ.get("PORT", 8080))

app = ApplicationBuilder().token(TOKEN).build()

# Attach all handlers: welcome, filters, admin commands, auto warn
setup_handlers(app)

# Start webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
)

print("🚀 LEGEND V6 ULTRA WEBHOOK LOADED")