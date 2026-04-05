import os
import json
import base64
import datetime
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
HF_TOKEN = "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"  # Your HuggingFace token

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        user = update.message.from_user.username or update.message.from_user.first_name
        
        # Download voice
        file = await context.bot.get_file(voice.file_id)
        voice_bytes = await file.download_as_bytearray()
        
        # FREE HuggingFace Whisper
        HF_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-tiny"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(HF_API_URL, headers=headers, data=voice_bytes)
        result = response.json()
        text = result[0]['text'] if isinstance(result, list) and len(result) > 0 else "No transcription"
        
        # Print to Railway logs (add Sheets later)
        now = datetime.datetime.now()
        print(f"{now} | {user} | {text}")
        
        await update.message.reply_text(f"✅ '{text}'")
        
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❌ Failed")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    print("🤖 FREE Transcription Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
