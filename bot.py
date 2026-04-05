import os
import requests
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = "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"  # Get free at console.groq.com

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Download voice
        file = await context.bot.get_file(update.message.voice.file_id)
        voice_bytes = await file.download_as_bytearray()
        
        # Groq Whisper (FREE, lightning fast)
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "whisper-large-v3",
            "audio": voice_bytes
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        text = result.get('text', 'No speech')
        
        await update.message.reply_text(f"✅ **{text}**")
        print(f"✅ {text}")
        
    except Exception as e:
        print(f"❌ {e}")
        await update.message.reply_text("❌ Try again")

app = Application.builder().token(TOKEN).build()
app.add_handler
