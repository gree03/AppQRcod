# AppQRcod

A minimal Telegram bot for managing invited guests.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `config.txt` with at least the bot token:
   ```
   BOT_TOKEN=123456:ABCDEF
   ADMIN_CHAT_ID=2194158282
   # DATABASE_PATH=./bot.db  # optional
   ```
3. Run the bot:
   ```bash
   python app.py
   ```

The bot will create the SQLite database if it does not exist.
