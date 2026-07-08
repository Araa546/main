import smtplib
import json
import os
import hashlib
import requests
import sys
import datetime
import pytz
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "8839353520:AAFAnpI2bw-1Eqi2UOh4vzk8txWiXkV8FYo"
FILE_CONFIG = "config.json"
DEVELOPER_ID = 1008449341
DEFAULT_PASSWORD = "hanania123"
BOT_NAME = "HANANIA REPORT" # UDAH DIGANTI
CURRENT_VERSION = "V12.5"
TIMEZONE = pytz.timezone("Asia/Jakarta")

LOGIN, MENU, KIRIM_REPORT, GANTI_FOTO, GANTI_AUDIO, ADD_EMAIL, ADD_PASS = range(7)

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
    msg = update.message or update.callback_query.message
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
    await update.message.reply_text("🔐 <b>Masukkan Kata Sandi Bot</b>\n\nPassword cukup 1x saja", parse_mode='HTML')
    return LOGIN

async def login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    password = update.message.text
    await update.message.delete()

    if hash_password(password) == config["bot_password_hash"]:
        keyboard = [
            [InlineKeyboardButton("📨 Kirim Laporan", callback_data='menu_send')],
            [InlineKeyboardButton("➕ Tambah Sender", callback_data='add_sender'), InlineKeyboardButton("📋 Sender Saya", callback_data='my_senders')],
            [InlineKeyboardButton("⚙️ Pengaturan", callback_data='menu_settings'), InlineKeyboardButton("📊 Status Bot", callback_data='menu_status')]
        ]
        if update.effective_user.id == DEVELOPER_ID:
            keyboard.append([InlineKeyboardButton("👑 PANEL OWNER ✨", callback_data='owner_panel')])

        username = update.effective_user.username or "User"
        try:
            await update.message.reply_photo(
                photo=config["foto_url"],
                caption=f"✨ <b>{BOT_NAME} {CURRENT_VERSION}</b> ✨\n\n👋 Selamat Datang @{username}\nID: <code>{update.effective_user.id}</code>\n\nSilakan pilih menu dibawah:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard),
                protect_content=True
            )
            await asyncio.sleep(0.3)
            await update.message.reply_audio(audio=config["audio_url"])
        except Exception as e: print(e)
        return MENU
    else:
        await update.message.reply_text("❌ Kata sandi salah. Ketik /start untuk coba lagi"); return ConversationHandler.END

async def add_email_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📧 <b>Langkah 1/2</b>\n\nKirim Email kamu dulu:", parse_mode='HTML')
    return ADD_EMAIL

async def add_email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if "@" not in email:
        await update.message.reply_text("❌ Format email salah. Kirim ulang:")
        return ADD_EMAIL
    context.user_data['temp_email'] = email
    await update.message.reply_text(f"✅ Email: <code>{email}</code>\n\n📧 <b>Langkah 2/2</b>\n\nSekarang kirim App Password nya:", parse_mode='HTML')
    return ADD_PASS

async def add_pass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    app_pass = update.message.text
    email = context.user_data['temp_email']
    config = load_config()
    config["senders"][email] = app_pass
    save_config(config)
    await update.message.delete()
    await update.message.reply_text(f"✅ <b>Sender Berhasil Ditambahkan!</b>\n\nEmail: <code>{email}</code>\nStatus: Aktif", parse_mode='HTML')
    return MENU

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id

    if query.data == 'menu_send':
        keyboard = [
            [InlineKeyboardButton("BR - BlackRock 🏦", callback_data='grupo_BR'), InlineKeyboardButton("SF - Solflare ☀️", callback_data='grupo_SF')],
            [InlineKeyboardButton("BI - Binance 🟡", callback_data='grupo_BI')],
            [InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data='back_menu')]
        ]
        await query.edit_message_text("📨 <b>Pilih Grup Untuk Laporan</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        return MENU

    elif query.data.startswith('grupo_'):
        grupo = query.data.split('_')[1]
        context.user_data['grupo'] = grupo
        await query.edit_message_text(f"✅ Grup: <b>{grupo}</b>\n\n📤 Kirim username/link Telegram yang mau direport:", parse_mode='HTML')
        return KIRIM_REPORT

    elif query.data == 'add_sender':
        await query.edit_message_text("➕ Gunakan command /addemail untuk tambah sender baru")
        return MENU

    elif query.data == 'my_senders':
        config = load_config()
        if not config["senders"]: text = "📋 Kamu belum punya Sender.\nGunakan /addemail"
        else: text = "📋 <b>Sender Saya:</b>\n\n" + "\n".join([f"• <code>{e}</code>" for e in config["senders"].keys()])
        await query.edit_message_text(text, parse_mode='HTML')
        return MENU

    elif query.data == 'menu_status':
        now = datetime.datetime.now(TIMEZONE).strftime("%H:%M")
        await query.edit_message_text(f"📊 <b>Status Bot</b>\n\nVersi: {CURRENT_VERSION}\nJam: {now} WIB\nStatus: Online ✅", parse_mode='HTML')
        return MENU

    elif query.data == 'owner_panel' and user_id == DEVELOPER_ID:
        keyboard = [
            [InlineKeyboardButton("🔄 Update Bot", callback_data='update_bot'), InlineKeyboardButton("📷 Ganti Foto", callback_data='ganti_foto')],
            [InlineKeyboardButton("🎵 Ganti Audio", callback_data='ganti_audio'), InlineKeyboardButton("⬅️ Kembali", callback_data='back_menu')]
        ]
        await query.edit_message_text("👑 <b>PANEL OWNER</b> ✨", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        return MENU

    elif query.data == 'update_bot' and user_id == DEVELOPER_ID:
        await update_bot(update, context)
        return MENU
    elif query.data == 'ganti_foto' and user_id == DEVELOPER_ID:
        await query.edit_message_text("📷 Kirim foto baru:"); return GANTI_FOTO
    elif query.data == 'ganti_audio' and user_id == DEVELOPER_ID:
        await query.edit_message_text("🎵 Kirim audio baru:"); return GANTI_AUDIO
    elif query.data == 'back_menu':
        keyboard = [[InlineKeyboardButton("📨 Kirim Laporan", callback_data='menu_send')]]
        await query.edit_message_text("Menu Utama:", reply_markup=InlineKeyboardMarkup(keyboard))
        return MENU
    return MENU

async def kirim_report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grupo = context.user_data.get('grupo')
    target = update.message.text
    await update.message.delete()
    await update.message.reply_text(f"✅ <b>Laporan Terkirim!</b>\n\nGrup: {grupo}\nTarget: <code>{target}</code>\nStatus: Menunggu diproses", parse_mode='HTML')
    return MENU

async def ganti_foto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID: return MENU
    photo = update.message.photo[-1]; file = await photo.get_file(); url = file.file_path
    config = load_config(); config["foto_url"] = url; save_config(config)
    await update.message.reply_text("✅ Foto berhasil diubah untuk semua user!"); return MENU

async def ganti_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID: return MENU
    audio = update.message.audio or update.message.document; file = await audio.get_file(); url = file.file_path
    config = load_config(); config["audio_url"] = url; save_config(config)
    await update.message.reply_text("✅ Audio berhasil diubah untuk semua user!"); return MENU

async def update_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update_bot(update, context)
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan."); context.user_data.clear(); return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # KUNCINYA: CallbackQueryHandler HARUS di luar ConversationHandler biar global
    app.add_handler(CommandHandler('update', update_bot_cmd))
    app.add_handler(CommandHandler('addemail', add_email_start))
    app.add_handler(CallbackQueryHandler(button_handler)) # PINDAH KE SINI

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_handler)],
            MENU: [], # MENU KOSONG, CUMA BUAT NAMPUNG STATE
            KIRIM_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, kirim_report_handler)],
            GANTI_FOTO: [MessageHandler(filters.PHOTO, ganti_foto_handler)],
            GANTI_AUDIO: [MessageHandler(filters.AUDIO | filters.Document.AUDIO, ganti_audio_handler)],
            ADD_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_email_handler)],
            ADD_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_pass_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)])
    app.add_handler(conv)
    print(f"{BOT_NAME} {CURRENT_VERSION} Jalan..."); app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
