import os
import requests
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler


TOKEN = os.getenv("TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

print(f"🚀 Starting bot...")
print(f"🚀 Token loaded: {'YES' if TOKEN else 'NO'}")
print(f"🚀 HF Token loaded: {'YES' if HF_TOKEN else 'NO'}")


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot working! Send 🎤 voice message.")


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("🎤 Voice message received!")

        # Download voice file
        file = await context.bot.get_file(update.message.voice.file_id)
        voice_bytes = await file.download_as_bytearray()
        print(f"📥 Downloaded {len(voice_bytes)} bytes")

        # Guard: check HF token is present
        print("HF token starts with:", HF_TOKEN[:4] if HF_TOKEN else "NONE")
        print("HF token length:", len(HF_TOKEN) if HF_TOKEN else 0)
    
        # HuggingFace Whisper API
        url = "https://api-inference.huggingface.co/models/openai/whisper-base"
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
        }

        response = requests.post(url, headers=headers, data=voice_bytes, timeout=120)

        print(f"📡 HF status: {response.status_code}")
        print(f"📡 HF response (head): {response.text[:350]}")

        if response.status_code == 503:
            await update.message.reply_text("⏳ Model is loading, try again in a few seconds.")
            return
        
        # Special handling for 410 / HTML error pages
        if response.status_code == 410:
            await update.message.reply_text(
                "⚠️ Hugging Face returned 410 Gone.\n"
                "This free Whisper endpoint may be unavailable.\n"
                "You might need to use a different model or endpoint."
            )
            return

        # If server returns HTML instead of JSON
        if "text/html" in response.headers.get("content-type", "").lower():
            await update.message.reply_text(
                "⚠️ Transcription failed with a web‑page error.\n"
                "Please check that your Hugging Face token is correct and has read access."
            )
            return

        if response.status_code != 200:
            await update.message.reply_text(
                f"⚠️ Transcription failed.\nStatus: {response.status_code}"
            )
            return

        try:
            data = response.json()
        except Exception:
            await update.message.reply_text(
                "⚠️ Error reading transcription response. Server returned invalid JSON."
            )
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
    if not TOKEN:
        print("🚨 No Telegram token set. Exiting.")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))

    print("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
