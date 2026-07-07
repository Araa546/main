 import smtplib
import json
import os
import hashlib
import requests
import io
import sys
import datetime
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "8839353520:AAFAnpI2bw-1Eqi2UOh4vzk8txWiXkV8FYo"
FILE_CONFIG = "config.json"
DEVELOPER_ID = 1008449341
DEFAULT_PASSWORD = "hanania123"
BOT_NAME = "BOT HANANIA REPORT"
CURRENT_VERSION = "V8.4"
TIMEZONE = pytz.timezone("Asia/Jakarta")

URL_VERSION = "https://raw.githubusercontent.com/Araa546/main/refs/heads/main/version.txt"
URL_REPORT = "https://raw.githubusercontent.com/Araa546/main/refs/heads/main/report.py"

LOGIN, GANTI_FOTO, GANTI_AUDIO = range(3)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_config():
    default = {
        "foto_url": "https://files.catbox.moe/qvonmj.jpg", # FOTO GLOBAL
        "audio_url": "https://files.catbox.moe/emfrvm.mp3", # AUDIO GLOBAL
        "bot_password_hash": hash_password(DEFAULT_PASSWORD),
        "senders": {},
        "whitelist": [DEVELOPER_ID],
        "banned": [],
        "version": CURRENT_VERSION,
        "maintenance_start": 23,
        "maintenance_end": 8,
        "groups": {
            "BR": [{"email": "informationsecurity@blackrock.com", "subject": "Report of Telegram Account Impersonating BlackRock Support"}],
            "SF": [{"email": "contact@solflare.com", "subject": "Report of Telegram Account Impersonating Solflare Support"}],
            "BI": [{"email": "phishing@binance.com", "subject": "Report Phishing Telegram Account"}]
        }
    }
    if os.path.exists(FILE_CONFIG):
        with open(FILE_CONFIG, 'r') as f:
            data = json.load(f)
            for key in default:
                if key not in data: data[key] = default[key]
            save_config(data)
            return data
    save_config(default)
    return default

def save_config(data):
    with open(FILE_CONFIG, 'w') as f:
        json.dump(data, f, indent=2)

def is_maintenance():
    config = load_config()
    now = datetime.datetime.now(TIMEZONE).hour
    start = config["maintenance_start"]
    end = config["maintenance_end"]
    if start > end: return now >= start or now < end
    else: return start <= now < end

async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID: return
    msg = update.message or update.callback_query.message
    await msg.reply_text("⏳ Download update dari github...")
    try:
        r = requests.get(URL_REPORT, timeout=10)
        with open("report.py", "w", encoding="utf-8") as f: f.write(r.text)
        await msg.reply_text("✅ Update selesai! Restart bot...")
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e: await msg.reply_text(f"❌ Gagal update: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if is_maintenance() and update.effective_user.id!= DEVELOPER_ID:
        await update.message.reply_text("🛠️ Bot sedang maintenance\nJam: 23.00 - 08.00 WIB")
        return ConversationHandler.END
    if update.effective_user.id in config.get("banned", []):
        await update.message.reply_text("🚫 Você foi banido."); return ConversationHandler.END

    # FOTO + AUDIO GLOBAL DARI CONFIG
    try:
        await update.message.reply_photo(photo=config["foto_url"], caption=f"🔒 <b>{BOT_NAME} {CURRENT_VERSION}</b>\n\nEste Bot é Privado", parse_mode='HTML')
        await update.message.reply_audio(audio=config["audio_url"])
    except: pass

    await update.message.reply_text("Digite a Senha untuk continuar:")
    return LOGIN

async def login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    password = update.message.text
    if hash_password(password) == config["bot_password_hash"]:
        keyboard = [[InlineKeyboardButton("📨 Send Report", callback_data='menu_send')]]
        if update.effective_user.id == DEVELOPER_ID:
            keyboard.append([InlineKeyboardButton("👑 OWNER PANEL", callback_data='owner_panel')])
        await update.message.reply_text("✅ Login berhasil!", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Senha salah. Coba lagi:"); return LOGIN

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id

    if query.data == 'owner_panel' and user_id == DEVELOPER_ID:
        keyboard = [[InlineKeyboardButton("🔄 Update Bot", callback_data='update_bot')],
                    [InlineKeyboardButton("📷 Ganti Foto GLOBAL", callback_data='ganti_foto')],
                    [InlineKeyboardButton("🎵 Ganti Audio GLOBAL", callback_data='ganti_audio')],
                    [InlineKeyboardButton("⬅️ Back", callback_data='back_menu')]]
        await query.edit_message_text("👑 OWNER PANEL\n\nNote: Ganti foto/audio akan berlaku untuk SEMUA USER", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'update_bot' and user_id == DEVELOPER_ID: await update_bot(update, context)
    elif query.data == 'ganti_foto' and user_id == DEVELOPER_ID:
        await query.edit_message_text("📷 Kirim foto baru. Foto ini akan dipakai semua user:"); return GANTI_FOTO
    elif query.data == 'ganti_audio' and user_id == DEVELOPER_ID:
        await query.edit_message_text("🎵 Kirim audio baru. Audio ini akan dipakai semua user:"); return GANTI_AUDIO

async def ganti_foto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID: return ConversationHandler.END
    photo = update.message.photo[-1]; file = await photo.get_file(); url = file.file_path
    config = load_config(); config["foto_url"] = url; save_config(config) # SIMPAN GLOBAL
    await update.message.reply_text("✅ Foto GLOBAL berhasil diganti!\nSemua user akan lihat foto baru pas /start")
    return ConversationHandler.END

async def ganti_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID: return ConversationHandler.END
    audio = update.message.audio or update.message.document; file = await audio.get_file(); url = file.file_path
    config = load_config(); config["audio_url"] = url; save_config(config) # SIMPAN GLOBAL
    await update.message.reply_text("✅ Audio GLOBAL berhasil diganti!\nSemua user akan dengar audio baru pas /start")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan."); context.user_data.clear(); return ConversationHandler.END

async def update_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update_bot(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('update', update_bot_cmd))
    conv_login = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_handler)],
                GANTI_FOTO: [MessageHandler(filters.PHOTO, ganti_foto_handler)],
                GANTI_AUDIO: [MessageHandler(filters.AUDIO | filters.Document.AUDIO, ganti_audio_handler)]},
        fallbacks=[CommandHandler('cancel', cancel)])
    app.add_handler(conv_login); app.add_handler(CallbackQueryHandler(button_handler))
    print(f"{BOT_NAME} {CURRENT_VERSION} Jalan..."); app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
