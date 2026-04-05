import os
import requests
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
HF_TOKEN = "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"  # ← PASTE YOUR HF TOKEN

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user.first_name
        print(f"Voice from {user}")
        
        # Download voice file
        file = await context.bot.get_file(update.message.voice.file_id)
        voice_bytes = await file.download_as_bytearray()
        
        # HuggingFace Whisper (free)
        url = "https://api-inference.huggingface.co/models/openai/whisper-tiny"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        response = requests.post(url, headers=headers, data=voice_bytes, timeout=60)
        
        # Handle HF queue/error
        if response.status_code == 503:
            await update.message.reply_text("⏳ Model loading... try in 30s")
            return
        if not response.ok:
            await update.message.reply_text("❌ API busy, try again")
            return
            
        result = response.json()
        text = result[0]['text'] if isinstance(result, list) and result else "No speech"
        
        await update.message.reply_text(f"✅ **{text}**")
        print(f"Transcribed: {text}")
        
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❌ Try again in 10s")

def main():
    # Fix conflict + timeouts
    app = Application.builder() \
        .token(TOKEN) \
        .read_timeout(30) \
        .write_timeout(30) \
        .connect_timeout(30) \
        .pool_timeout(30) \
        .build()
    
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    print("🤖 Bot ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
