# bot.py
import asyncio
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import whisper

# ------------------------------
# GOOGLE SHEETS SETUP
# ------------------------------

# Put your credentials file here (same folder as bot.py)
CREDENTIALS_FILE = "credentials.json"

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# Open your sheet (must match the name exactly)
sheet = client.open("Voice Logs").sheet1

# ------------------------------
# WHISPER MODEL SETUP
# ------------------------------

model = whisper.load_model("base")  # or tiny, small, medium, large

# ------------------------------
# TELEGRAM BOT TOKEN
# ------------------------------

TOKEN = "8305367371:AAHyGPbS3g7i2ZCGGQrh9uL8aG4nXzrAw4A"  # <- replace this with your bot token

# ------------------------------
# VOICE HANDLER
# ------------------------------

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("🎤 Voice received")

        voice = update.message.voice
        user = update.message.from_user.username or update.message.from_user.first_name

        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive("voice.ogg")
        print("⬇️ Downloaded voice file")

        result = model.transcribe("voice.ogg")
        text = result["text"]
        print("🧠 Transcribed:", text)

        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        sheet.append_row([date, time, user, text])
        print("📄 Saved to Google Sheets")

        await update.message.reply_text("✅ Saved to Google Sheets!")

    except Exception as e:
        print("❌ ERROR:", e)
        await update.message.reply_text("❌ Error occurred. Check terminal.")

# ------------------------------
# RUN BOT
# ------------------------------

app = Application.builder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.VOICE, voice_handler))

print("🤖 Bot is running...")

app.run_polling()