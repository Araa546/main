import smtplib
import json
import os
import hashlib
import requests
import sys
import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "8839353520:AAFAnpI2bw-1Eqi2UOh4vzk8txWiXkV8FYo"
FILE_CONFIG = "config.json"
DEVELOPER_ID = 1008449341
DEFAULT_PASSWORD = "hanania123"
BOT_NAME = "BOT HANANIA REPORT"
CURRENT_VERSION = "V8.11"
TIMEZONE = pytz.timezone("Asia/Jakarta")

LOGIN, GANTI_FOTO, GANTI_AUDIO, KIRIM_REPORT = range(4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_config():
    default = {"foto_url": "https://files.catbox.moe/qvonmj.jpg", "audio_url": "https://files.catbox.moe/emfrvm.mp3", "bot_password_hash": hash_password(DEFAULT_PASSWORD), "senders": {}, "whitelist": [DEVELOPER_ID], "banned": [], "version": CURRENT_VERSION, "maintenance_start": 23.5, "maintenance_end": 8.0, "groups": {"BR": [{"email": "informationsecurity@blackrock.com", "subject": "Laporan Akun Telegram Yang Mengatasnamakan BlackRock"}], "SF": [{"email": "contact@solflare.com", "subject": "Laporan Akun Telegram Yang Mengatasnamakan Solflare"}], "BI": [{"email": "phishing@binance.com", "subject": "Laporan Phishing Akun Telegram"}]}}
    if os.path.exists(FILE_CONFIG):
        with open(FILE_CONFIG, 'r') as f: data = json.load(f)
        for key in default:
            if key not in data: data[key] = default[key]
        save_config(data); return data
    save_config(default); return default

def save_config(data):
    with open(FILE_CONFIG, 'w') as f: json.dump(data, f, indent=2)

def is_maintenance():
    config = load_config()
    now = datetime.datetime.now(TIMEZONE)
    now_float = now.hour + now.minute / 60.0
    start = config["maintenance_start"]; end = config["maintenance_end"]
    if start > end: return now_float >= start or now_float < end
    else: return start <= now_float < end

async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID: return

    # FIX ERROR: biar bisa dari message dan callback
    if update.message:
        msg = update.message
    else:
        msg = update.callback_query.message

    await msg.reply_text("⏳ Sedang mengunduh pembaruan dari github...")
    try:
        r = requests.get("https://raw.githubusercontent.com/Araa546/main/refs/heads/main/report.py", timeout=10)
        with open("report.py", "w", encoding="utf-8") as f: f.write(r.text)
        await msg.reply_text("✅ Pembaruan selesai! Bot akan restart...")
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e: await msg.reply_text(f"❌ Gagal update: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if is_maintenance() and update.effective_user.id!= DEVELOPER_ID:
        now = datetime.datetime.now(TIMEZONE).strftime("%H:%M")
        await update.message.reply_text(f"🛠️ BOT SEDANG DALAM PERAWATAN\nJam sekarang: {now} WIB\nSilakan kembali jam 08:00 WIB\nTerima kasih 🙏"); return ConversationHandler.END
    if update.effective_user.id in config.get("banned", []):
        await update.message.reply_text("🚫 Anda telah dibanned."); return ConversationHandler.END
    await update.message.reply_text("🔒 Masukkan Kata Sandi untuk melanjutkan:"); return LOGIN

async def login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    password = update.message.text
    if hash_password(password) == config["bot_password_hash"]:
        try:
            await update.message.reply_photo(photo=config["foto_url"], caption=f"🔒 <b>{BOT_NAME} {CURRENT_VERSION}</b>\n\nSelamat Datang!", parse_mode='HTML')
            await update.message.reply_audio(audio=config["audio_url"])
        except: pass

        keyboard = [
            [InlineKeyboardButton("📨 Kirim Laporan", callback_data='menu_send'), InlineKeyboardButton("➕ Tambah Sender", callback_data='add_sender')],
            [InlineKeyboardButton("📋 Sender Saya", callback_data='my_senders'), InlineKeyboardButton("⚙️ Pengaturan", callback_data='menu_settings')],
            [InlineKeyboardButton("📊 Status Bot", callback_data='menu_status')]
        ]
        if update.effective_user.id == DEVELOPER_ID:
            keyboard.append([InlineKeyboardButton("👑 PANEL OWNER", callback_data='owner_panel')])

        await update.message.reply_text("✅ Login berhasil! Pilih menu:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Kata sandi salah. Coba lagi:"); return LOGIN

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id

    if query.data == 'menu_send':
        keyboard = [
            [InlineKeyboardButton("BR - BlackRock", callback_data='grupo_BR'), InlineKeyboardButton("SF - Solflare", callback_data='grupo_SF')],
            [InlineKeyboardButton("BI - Binance", callback_data='grupo_BI'), InlineKeyboardButton("⬅️ Kembali", callback_data='back_menu')]
        ]
        await query.edit_message_text("📨 Pilih grup untuk kirim laporan:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('grupo_'):
        grupo = query.data.split('_')[1]
        context.user_data['grupo'] = grupo
        await query.edit_message_text(f"✅ Grup: {grupo}\n\nSekarang kirim username/link Telegram yang mau direport:")
        return KIRIM_REPORT

    elif query.data == 'add_sender':
        await query.edit_message_text("➕ Kirim format:\n`email|password_app`\nContoh: `email@gmail.com|abcd efgh ijkl mnop`", parse_mode='Markdown')

    elif query.data == 'my_senders':
        config = load_config()
        if not config["senders"]: await query.edit_message_text("📋 Kamu belum punya Sender.")
        else:
            text = "📋 **Sender Saya:**\n\n" + "\n".join([f"- `{e}`" for e in config["senders"].keys()])
            await query.edit_message_text(text, parse_mode='Markdown')

    elif query.data == 'menu_settings':
        await query.edit_message_text("⚙️ Pengaturan:\n\nSegera hadir...")

    elif query.data == 'menu_status':
        now = datetime.datetime.now(TIMEZONE).strftime("%H:%M")
        await query.edit_message_text(f"📊 **Status Bot**\n\nVersi: {CURRENT_VERSION}\nJam: {now} WIB\nStatus: Online ✅", parse_mode='Markdown')

    elif query.data == 'owner_panel' and user_id == DEVELOPER_ID:
        keyboard = [
            [InlineKeyboardButton("🔄 Update Bot", callback_data='update_bot'), InlineKeyboardButton("📷 Ganti Foto", callback_data='ganti_foto')],
            [InlineKeyboardButton("🎵 Ganti Audio", callback_data='ganti_audio'), InlineKeyboardButton("⬅️ Kembali", callback_data='back_menu')]
        ]
        await query.edit_message_text("👑 PANEL OWNER", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'update_bot' and user_id == DEVELOPER_ID: await update_bot(update, context)
    elif query.data == 'ganti_foto' and user_id == DEVELOPER_ID:
        await query.edit_message_text("📷 Kirim foto baru:"); return GANTI_FOTO
    elif query.data == 'ganti_audio' and user_id == DEVELOPER_ID:
        await query.edit_message_text("🎵 Kirim audio baru:"); return GANTI_AUDIO
    elif query.data == 'back_menu':
        keyboard = [[InlineKeyboardButton("📨 Kirim Laporan", callback_data='menu_send')]]
        await query.edit_message_text("Menu Utama:", reply_markup=InlineKeyboardMarkup(keyboard))

async def kirim_report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grupo = context.user_data.get('grupo')
    target = update.message.text
    await update.message.reply_text(f"✅ Laporan untuk grup {grupo} diterima!\nTarget: {target}\n\nFitur kirim email belum diaktifkan.")
    return ConversationHandler.END

async def ganti_foto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID: return ConversationHandler.END
    photo = update.message.photo[-1]; file = await photo.get_file(); url = file.file_path
    config = load_config(); config["foto_url"] = url; save_config(config)
    await update.message.reply_text("✅ Foto berhasil diubah untuk semua user!"); return ConversationHandler.END

async def ganti_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID: return ConversationHandler.END
    audio = update.message.audio or update.message.document; file = await audio.get_file(); url = file.file_path
    config = load_config(); config["audio_url"] = url; save_config(config)
    await update.message.reply_text("✅ Audio berhasil diubah untuk semua user!"); return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan."); context.user_data.clear(); return ConversationHandler.END

async def update_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await update_bot(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('update', update_bot_cmd))
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_handler)],
                KIRIM_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, kirim_report_handler)],
                GANTI_FOTO: [MessageHandler(filters.PHOTO, ganti_foto_handler)],
                GANTI_AUDIO: [MessageHandler(filters.AUDIO | filters.Document.AUDIO, ganti_audio_handler)]},
        fallbacks=[CommandHandler('cancel', cancel)])
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_handler))
    print(f"{BOT_NAME} {CURRENT_VERSION} Jalan..."); app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
