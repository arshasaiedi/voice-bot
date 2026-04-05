import os
import json
import base64
import datetime
import asyncio
import tempfile

import gspread
import whisper
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Get secrets from Railway environment variables
TOKEN = os.getenv("TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

if not TOKEN:
    raise ValueError("TOKEN environment variable is missing")
if not GOOGLE_CREDENTIALS:
    raise ValueError("GOOGLE_CREDENTIALS environment variable is missing")

# Load Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds_json = json.loads(base64.b64decode(GOOGLE_CREDENTIALS).decode())
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open("Voice Logs").sheet1

# Load Whisper model
model = whisper.load_model("base")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("Voice received")
        voice = update.message.voice
        user = update.message.from_user.username or update.message.from_user.first_name

        tg_file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            audio_path = tmp.name

        await tg_file.download_to_drive(custom_path=audio_path)
        print("Downloaded voice file")

        text = await asyncio.to_thread(lambda: model.transcribe(audio_path)["text"])
        print("Transcribed:", text)

        now = datetime.datetime.now()
        sheet.append_row([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            user,
            text,
        ])
        print("Saved to Google Sheets")

        await update.message.reply_text("✅ Saved to Google Sheets!")

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("❌ Error occurred. Check logs.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
