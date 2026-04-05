import os
import json
import base64
import datetime
import io
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

TOKEN = os.getenv("TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(base64.b64decode(GOOGLE_CREDENTIALS).decode())
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open("Voice Logs").sheet1

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        user = update.message.from_user.username or update.message.from_user.first_name
        
        # Download voice file
        file = await context.bot.get_file(voice.file_id)
        voice_bytes = await file.download_as_bytearray()
        
        # Use FREE HuggingFace Whisper API
        HF_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-tiny"
        headers = {"Authorization": "Bearer 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"}  # Get free token at huggingface.co
        
        response = requests.post(HF_API_URL, headers=headers, data=voice_bytes)
        result = response.json()
        text = result[0]['text'] if result else "Could not transcribe"
        
        # Save to Google Sheets
        now = datetime.datetime.now()
        sheet.append_row([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            user,
            text
        ])
        
        await update.message.reply_text(f"✅ Transcribed: '{text}'")
        print(f"{user}: {text}")
        
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❌ Transcription failed")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    print("🤖 FREE Voice Transcription Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
