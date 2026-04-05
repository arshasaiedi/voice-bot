import os
import json
import base64
import datetime
import tempfile
import wave
import pydub
from vosk import Model, KaldiRecognizer
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

if not TOKEN or not GOOGLE_CREDENTIALS:
    raise ValueError("Missing environment variables")

# Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(base64.b64decode(GOOGLE_CREDENTIALS).decode())
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open("Voice Logs").sheet1

# Vosk (free, offline, tiny)
model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("Voice received")
        voice = update.message.voice
        user = update.message.from_user.username or update.message.from_user.first_name

        # Download voice
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)

        # Convert ogg → wav → transcribe
        audio = pydub.AudioSegment.from_ogg(tmp.name)
        audio = audio.set_frame_rate(16000).set_channels(1)
        wav_path = tmp.name.replace('.ogg', '.wav')
        audio.export(wav_path, format="wav")

        # Transcribe with Vosk
        wf = wave.open(wav_path, "rb")
        text = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text += json.loads(result)["text"] + " "

        # Save to sheet
        now = datetime.datetime.now()
        sheet.append_row([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            user,
            text.strip()
        ])

        print(f"Transcribed: {text}")
        await update.message.reply_text(f"✅ '{text}' saved!")

        # Cleanup
        os.unlink(tmp.name)
        os.unlink(wav_path)

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("❌ Error occurred")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    print("🤖 FREE Voice Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
