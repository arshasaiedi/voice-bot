import os
import requests
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler

# Load from Railway
TOKEN = os.getenv("TOKEN")
HF_TOKEN = "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"  # ← PASTE YOUR HUGGINGFACE TOKEN

print(f"🚀 Starting bot...")
print(f"🚀 Token loaded: {'YES' if TOKEN else 'NO'}")
print(f"🚀 HF Token loaded: {'YES' if HF_TOKEN != 'hf_YOUR_FULL_HF_TOKEN_HERE' else 'NO'}")

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot working! Send 🎤 voice message.")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("🎤 Voice message received!")

        # Download voice file
        file = await context.bot.get_file(update.message.voice.file_id)
        voice_bytes = await file.download_as_bytearray()
        print(f"📥 Downloaded {len(voice_bytes)} bytes")

        # HuggingFace Whisper API
        url = "https://api-inference.huggingface.co/models/openai/whisper-tiny"
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "audio/ogg",
        }

        response = requests.post(url, headers=headers, data=voice_bytes, timeout=120)

        print(f"📡 HF status: {response.status_code}")
        print(f"📡 HF response: {response.text[:300]}")

        if response.status_code != 200:
            await update.message.reply_text(f"⚠️ Transcription failed.\nStatus: {response.status_code}")
            return

        try:
            data = response.json()
        except Exception:
            await update.message.reply_text("⚠️ Error reading transcription response.")
            return

        text = data.get("text", "").strip()

        if not text:
            await update.message.reply_text("⚠️ No speech detected.")
            return

        await update.message.reply_text(f"📝 Transcript:\n\n{text}")

    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    print("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
