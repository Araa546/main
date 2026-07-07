import smtplib
import json
import os
import hashlib
import requests
import io
import sys
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "8839353520:AAFAnpI2bw-1Eqi2UOh4vzk8txWiXkV8FYo"
FILE_CONFIG = "config.json"
PREMIUM_EMOJI_ID = "5440621591387980068"
DEVELOPER_NAME = "@nanialagibobo"
DEVELOPER_ID = 1008449341
DEFAULT_PASSWORD = "hanania123"
BOT_NAME = "BOT HANANIA REPORT"
CURRENT_VERSION = "V7.8.3"

URL_VERSION = "https://raw.githubusercontent.com/Araa546/main/refs/heads/main/version.txt"
URL_REPORT = "https://raw.githubusercontent.com/Araa546/main/refs/heads/main/report.py"

LOGIN, MT, EMAIL, PASSWORD, ADD_EMAIL, GANTI_FOTO, GANTI_AUDIO, MAINTENANCE = range(8)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_config():
    default = {
        "foto_url": "https://files.catbox.moe/qvonmj.jpg",
        "audio_url": "https://files.catbox.moe/emfrvm.mp3",
        "bot_password_hash": hash_password(DEFAULT_PASSWORD),
        "senders": {},
        "whitelist": [1008449341, DEVELOPER_ID],
        "banned": [],
        "version": CURRENT_VERSION,
        "maintenance": False,
        "groups": {
            "BR": [
                {"email": "informationsecurity@blackrock.com", "subject": "Report of Telegram Account Impersonating BlackRock Support"},
                {"email": "reportascam@blackrock.com", "subject": "Report of Telegram Account Impersonating BlackRock Support"}
            ],
            "SF": [{"email": "contact@solflare.com", "subject": "Report of Telegram Account Impersonating Solflare Support"}],
            "BI": [{"email": "phishing@binance.com", "subject": "Report Phishing Telegram Account"}]
        }
    }
    if os.path.exists(FILE_CONFIG):
        with open(FILE_CONFIG, 'r') as f:
            data = json.load(f)
            for key in default:
                if key not in data:
                    data[key] = default[key]
            data["foto_url"] = "https://files.catbox.moe/qvonmj.jpg"
            data["version"] = CURRENT_VERSION
            save_config(data)
            return data
    save_config(default)
    return default

def save_config(data):
    with open(FILE_CONFIG, 'w') as f:
        json.dump(data, f, indent=2)

def premium_emoji(text):
    return f'&#{PREMIUM_EMOJI_ID};{text}'

def get_user_senders(config, user_id):
    user_id_str = str(user_id)
    if user_id_str not in config["senders"]:
        config["senders"][user_id_str] = []
    return config["senders"][user_id_str]

def check_update():
    try:
        r = requests.get(URL_VERSION, timeout=5)
        latest = r.text.strip()
        if latest!= CURRENT_VERSION:
            return latest
    except:
        pass
    return None

async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID:
        msg = update.message or update.callback_query.message
        await msg.reply_text("❌ Hanya owner")
        return
    msg = update.message or update.callback_query.message
    await msg.reply_text("⏳ Download update dari github...")
    try:
        r = requests.get(URL_REPORT, timeout=10)
        if r.status_code!= 200:
            await msg.reply_text(f"❌ Gagal: HTTP {r.status_code}")
            return
        with open("report.py", "w", encoding="utf-8") as f:
            f.write(r.text)
        await msg.reply_text("✅ Update selesai! Restart bot...")
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        await msg.reply_text(f"❌ Gagal update: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan.")
    context.user_data.clear()
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if config.get("maintenance") and update.effective_user.id!= DEVELOPER_ID:
        await update.message.reply_text("🛠️ Bot sedang maintenance")
        return ConversationHandler.END
    if update.effective_user.id in config.get("banned", []):
        await update.message.reply_text("🚫 Você foi banido.")
        return ConversationHandler.END
    latest = check_update()
    if latest and update.effective_user.id == DEVELOPER_ID:
        await update.message.reply_text(f"🆕 Update tersedia: {latest}\nKetik /update untuk update otomatis")
    await update.message.reply_text(f"🔒 <b>{BOT_NAME} {CURRENT_VERSION}</b>\n\nEste Bot é Privado\nDigite a Senha untuk continuar:", parse_mode='HTML')
    return LOGIN

async def login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    password = update.message.text
    if hash_password(password) == config["bot_password_hash"]:
        keyboard = [[InlineKeyboardButton("📨 Send Report", callback_data='menu_send')],
                    [InlineKeyboardButton("⚙️ Settings", callback_data='menu_settings')]]
        if update.effective_user.id == DEVELOPER_ID:
            keyboard.append([InlineKeyboardButton("👑 OWNER PANEL", callback_data='owner_panel')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("✅ Login berhasil!", reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Senha salah. Coba lagi:")
        return LOGIN

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = load_config()
    user_id = query.from_user.id

    if query.data == 'owner_panel' and user_id == DEVELOPER_ID:
        keyboard = [[InlineKeyboardButton("🔄 Update Bot", callback_data='update_bot')],
                    [InlineKeyboardButton("📷 Ganti Foto", callback_data='ganti_foto')],
                    [InlineKeyboardButton("🎵 Ganti Audio", callback_data='ganti_audio')],
                    [InlineKeyboardButton("🛠️ Maintenance", callback_data='maintenance')],
                    [InlineKeyboardButton("⬅️ Back", callback_data='back_menu')]]
        await query.edit_message_text("👑 OWNER PANEL", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'update_bot' and user_id == DEVELOPER_ID:
        await update_bot(update, context)

    elif query.data == 'ganti_foto':
        await query.edit_message_text("📷 Kirim foto baru:")
        return GANTI_FOTO

    elif query.data == 'ganti_audio':
        await query.edit_message_text("🎵 Kirim file audio baru:")
        return GANTI_AUDIO

    elif query.data == 'maintenance':
        config["maintenance"] = not config["maintenance"]
        status = "ON" if config["maintenance"] else "OFF"
        save_config(config)
        await query.edit_message_text(f"🛠️ Maintenance: {status}")

    elif query.data == 'back_menu':
        keyboard = [[InlineKeyboardButton("📨 Send Report", callback_data='menu_send')],
                    [InlineKeyboardButton("⚙️ Settings", callback_data='menu_settings')]]
        if user_id == DEVELOPER_ID:
            keyboard.append([InlineKeyboardButton("👑 OWNER PANEL", callback_data='owner_panel')])
        await query.edit_message_text("Menu Utama:", reply_markup=InlineKeyboardMarkup(keyboard))

async def ganti_foto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    url = file.file_path
    config = load_config()
    config["foto_url"] = url
    save_config(config)
    await update.message.reply_text("✅ Foto berhasil diganti")
    return ConversationHandler.END

async def ganti_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio = update.message.audio or update.message.document
    file = await audio.get_file()
    url = file.file_path
    config = load_config()
    config["audio_url"] = url
    save_config(config)
    await update.message.reply_text("✅ Audio berhasil diganti")
    return ConversationHandler.END

async def update_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update_bot(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('update', update_bot_cmd))

    conv_login = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_handler)],
            GANTI_FOTO: [MessageHandler(filters.PHOTO, ganti_foto_handler)],
            GANTI_AUDIO: [MessageHandler(filters.AUDIO | filters.Document.AUDIO, ganti_audio_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_login)
    app.add_handler(CallbackQueryHandler(button_handler))

    print(f"{BOT_NAME} {CURRENT_VERSION} Jalan...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
