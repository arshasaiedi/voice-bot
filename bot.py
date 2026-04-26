import os
import requests
import datetime
import json

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler

import gspread
from google.oauth2.service_account import Credentials


# 🔐 ENV VARIABLES
TOKEN = os.getenv("TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")


print("🚀 Starting bot...")
print(f"TOKEN loaded: {'YES' if TOKEN else 'NO'}")
print(f"HF_TOKEN loaded: {'YES' if HF_TOKEN else 'NO'}")
print(f"GOOGLE creds loaded: {'YES' if GOOGLE_CREDENTIALS else 'NO'}")


# 📊 GOOGLE SHEETS SETUP
scopes = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=scopes
)

client = gspread.authorize(creds)

# ⚠️ CHANGE THIS to your sheet name
sheet = client.open("Voice Transcriptions").sheet1


# ▶️ /start command
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot working! Send a voice message 🎤")


# 🎤 Voice handler
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("🎤 Voice received")

        # 📥 Download voice file
        file = await context.bot.get_file(update.message.voice.file_id)
        voice_bytes = await file.download_as_bytearray()

        print(f"Downloaded {len(voice_bytes)} bytes")

        # 🤖 Hugging Face Whisper
        url = "https://api-inference.huggingface.co/models/openai/whisper-base"

        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
        }

        response = requests.post(url, headers=headers, data=voice_bytes, timeout=120)

        print("HF status:", response.status_code)
        print("HF response:", response.text[:300])

        # ⏳ Model loading
        if response.status_code == 503:
            await update.message.reply_text("⏳ Model is loading, try again in a few seconds.")
            return

        # ❌ Bad response
        if "text/html" in response.headers.get("content-type", "").lower():
            await update.message.reply_text("⚠️ Hugging Face returned an error page.")
            return

        if response.status_code != 200:
            await update.message.reply_text(f"⚠️ Error: {response.status_code}")
            return

        # 🧠 Parse transcription
        data = response.json()
        text = data.get("text", "").strip()

        if not text:
            await update.message.reply_text("⚠️ No speech detected.")
            return

        # 📊 Save to Google Sheets
        sheet.append_row([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            text
        ])

        # 📤 Reply to user
        await update.message.reply_text(f"📝 {text}")

    except Exception as e:
        print("❌ Error:", e)
        await update.message.reply_text(f"❌ Error: {str(e)}")


# 🚀 Main
def main():
    if not TOKEN:
        print("No Telegram token!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    print("🤖 Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
