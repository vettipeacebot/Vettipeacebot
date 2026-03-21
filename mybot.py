# mybot.py
import os
from mybot_logic import main  # Import all logic from mybot_logic.py

print("🚀 LEGEND V6 ULTRA BOT STARTING 🚀")

if __name__ == "__main__":
    # Make sure your environment variables are set:
    # BOT_TOKEN -> your bot token
    # PORT -> port for webhook (Railway default 8443)
    # WEBHOOK_URL -> your public Railway domain
    main()