import json
import os
import hashlib
import smtplib
import datetime
import pytz
import asyncio
import aiohttp
from email.mime.text import MIMEText
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8839353520:AAFAnpI2bw-1Eqi2UOh4vzk8txWiXkV8FYo"
FILE_CONFIG = "config.json"
FILE_LOGS = "logs.json" # FILE BARU BUAT SIMPEN USER YANG UDAH LOGIN
DEVELOPER_ID = 1008449341
DEFAULT_PASSWORD = "hanania123"
BOT_NAME = "HANANIA REPORT"
CURRENT_VERSION = "V13.9"
TIMEZONE = pytz.timezone("Asia/Jakarta")

USER_STATE = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_config():
    default = {
        "foto_url": "https://files.catbox.moe/qvonmj.jpg",
        "audio_url": "https://files.catbox.moe/emfrvm.mp3",
        "bot_password_hash": hash_password(DEFAULT_PASSWORD),
        "senders": {},
        "banned": [],
        "groups": {
            "BR": [
                {"email": "informationsecurity@blackrock.com", "subject": "Report of Telegram Account Impersonating BlackRock Support"},
                {"email": "reportascam@blackrock.com", "subject": "Report of Telegram Account Impersonating BlackRock Support"}
            ],
            "SF": [{"email": "contact@solflare.com", "subject": "Report of Telegram Account Impersonating Solflare"}],
            "BI": [{"email": "phishing@binance.com", "subject": "Report of Telegram Account Impersonating Binance"}]
        }
    }
    if os.path.exists(FILE_CONFIG):
        with open(FILE_CONFIG, 'r') as f: data = json.load(f)
        for key in default:
            if key not in data: data[key] = default[key]
        save_config(data); return data
    save_config(default); return default

def save_config(data):
    with open(FILE_CONFIG, 'w') as f: json.dump(data, f, indent=2)

def load_logs(): # BUAT BACA SIAPA AJA YANG UDAH LOGIN
    if os.path.exists(FILE_LOGS):
        with open(FILE_LOGS, 'r') as f: return json.load(f)
    return {"logged_users": []}

def save_logs(data): # BUAT SIMPEN ID USER YANG UDAH LOGIN
    with open(FILE_LOGS, 'w') as f: json.dump(data, f, indent=2)

async def upload_to_catbox(file_bytes, filename):
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('reqtype', 'fileupload')
            data.add_field('fileToUpload', file_bytes, filename=filename)
            async with session.post('https://catbox.moe/user/api.php', data=data) as resp:
                return await resp.text()
    except:
        return None

async def kirim_email(sender_email, app_password, to_email, subject, body):
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_email
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

async def show_menu(context: ContextTypes.DEFAULT_TYPE, chat_id, user):
    config = load_config()
    keyboard = [
        [InlineKeyboardButton("📨 Kirim Laporan", callback_data='menu_send')],
        [InlineKeyboardButton("➕ Tambah Sender", callback_data='add_sender'), InlineKeyboardButton("📋 Sender Saya", callback_data='my_senders')],
        [InlineKeyboardButton("📊 Status Bot", callback_data='menu_status')]
    ]
    if user.id == DEVELOPER_ID:
        keyboard.append([InlineKeyboardButton("👑 PANEL OWNER ✨", callback_data='owner_panel')])

    username = user.username or "User"
    caption = f"✨ <b>{BOT_NAME} {CURRENT_VERSION}</b> ✨\n\n👋 Selamat Datang @{username}\nID: <code>{user.id}</code>\n\nSilakan pilih menu dibawah:"

    try:
        if config["foto_url"]:
            await context.bot.send_photo(chat_id=chat_id, photo=config["foto_url"], caption=caption, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard), protect_content=True)
        else:
            await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        if config["audio_url"]:
            await asyncio.sleep(0.3)
            await context.bot.send_audio(chat_id=chat_id, audio=config["audio_url"], protect_content=True)
    except Exception as e:
        print(f"Error show_menu: {e}")
        await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    config = load_config()
    logs = load_logs()

    if user_id in config.get("banned", []):
        await update.message.reply_text("🚫 Anda telah dibanned."); return

    # CEK APAKAH USER SUDAH PERNAH LOGIN
    if user_id in logs["logged_users"]:
        USER_STATE[user_id] = "MENU"
        await update.message.reply_text("✅ <b>Selamat Datang Kembali!</b>\nAuto login berhasil.", parse_mode='HTML')
        await show_menu(context, update.effective_chat.id, update.effective_user)
    else:
        USER_STATE[user_id] = "LOGIN"
        await update.message.reply_text("🔐 <b>Masukkan Kata Sandi Bot</b>\n\nPassword cukup 1x saja. Nanti auto login", parse_mode='HTML')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = USER_STATE.get(user_id)
    config = load_config()

    if state == "LOGIN":
        await update.message.delete()
        if hash_password(text) == config["bot_password_hash"]:
            # SIMPAN ID KE LOGS BIAR GA LOGIN LAGI
            logs = load_logs()
            if user_id not in logs["logged_users"]:
                logs["logged_users"].append(user_id)
                save_logs(logs)

            USER_STATE[user_id] = "MENU"
            await update.message.reply_text("✅ <b>Login Berhasil!</b>\nBesok /start langsung masuk menu.", parse_mode='HTML')
            await show_menu(context, update.effective_chat.id, update.effective_user)
        else:
            await update.message.reply_text("❌ Kata sandi salah. Ketik /start untuk coba lagi")

    elif state == "ADD_EMAIL":
        if "@" not in text or "." not in text:
            await update.message.reply_text("❌ Format email salah. Kirim ulang:"); return
        context.user_data['temp_email'] = text
        USER_STATE[user_id] = "ADD_PASS"
        await update.message.reply_text(f"✅ Email: <code>{text}</code>\n\n📧 <b>Langkah 2/2</b>\n\nSekarang kirim App Password 16 digit:", parse_mode='HTML')

    elif state == "ADD_PASS":
        email = context.user_data['temp_email']
        app_pass = text.replace(" ", "")
        config["senders"][email] = app_pass
        save_config(config)
        await update.message.delete()
        USER_STATE[user_id] = "MENU"
        await update.message.reply_text(f"✅ <b>Sender Berhasil Ditambahkan!</b>\n\nEmail: <code>{email}</code>\nStatus: Aktif", parse_mode='HTML')
        await show_menu(context, update.effective_chat.id, update.effective_user)

    elif state == "KIRIM_REPORT":
        grupo = context.user_data.get('grupo')
        target = text
        await update.message.delete()
        msg = await update.message.reply_text("⏳ <b>Sedang mengirim laporan...</b>\nMohon tunggu", parse_mode='HTML')
        config = load_config()
        senders = config["senders"]
        group_emails = config["groups"].get(grupo, [])
        sukses = 0; gagal = 0
        if not senders:
            await msg.edit_text("❌ Kamu belum punya sender. Tambah dulu di menu 'Tambah Sender'")
            USER_STATE[user_id] = "MENU"; await show_menu(context, update.effective_chat.id, update.effective_user); return
        for sender_email, app_pass in senders.items():
            for grup in group_emails:
                body = f"Yth Tim Keamanan,\n\nSaya ingin melaporkan akun telegram yang mengatasnamakan {grupo}.\n\nDetail Akun:\n{target}\n\nTerima kasih."
                status = await kirim_email(sender_email, app_pass, grup['email'], grup['subject'], body)
                if status: sukses += 1
                else: gagal += 1
                await asyncio.sleep(2)
        result = f"✅ <b>LAPORAN SELESAI</b>\n\n🎯 Grup: <b>{grupo}</b>\n👤 Target: <code>{target}</code>\n\n📊 <b>HASIL PENGIRIMAN</b>\n✅ Sukses: <b>{sukses}</b>\n❌ Gagal: <b>{gagal}</b>\n📧 Total: <b>{sukses + gagal}</b>"
        await msg.edit_text(result, parse_mode='HTML')
        USER_STATE[user_id] = "MENU"; await show_menu(context, update.effective_chat.id, update.effective_user)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if USER_STATE.get(user_id) == "GANTI_FOTO" and user_id == DEVELOPER_ID:
        photo = update.message.photo[-1]; file = await photo.get_file(); file_bytes = await file.download_as_bytearray()
        await update.message.reply_text("⏳ Mengupload foto ke catbox...")
        url = await upload_to_catbox(file_bytes, "menu.jpg")
        if url: config = load_config(); config["foto_url"] = url; save_config(config); await update.message.reply_text(f"✅ Foto berhasil diubah!\nLink: {url}", protect_content=True)
        else: await update.message.reply_text("❌ Gagal upload foto")
        USER_STATE[user_id] = "MENU"; await show_menu(context, update.effective_chat.id, update.effective_user)

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if USER_STATE.get(user_id) == "GANTI_AUDIO" and user_id == DEVELOPER_ID:
        audio = update.message.audio or update.message.document; file = await audio.get_file(); file_bytes = await file.download_as_bytearray()
        await update.message.reply_text("⏳ Mengupload audio ke catbox...")
        url = await upload_to_catbox(file_bytes, "menu.mp3")
        if url: config = load_config(); config["audio_url"] = url; save_config(config); await update.message.reply_text(f"✅ Audio berhasil diubah!\nLink: {url}", protect_content=True)
        else: await update.message.reply_text("❌ Gagal upload audio")
        USER_STATE[user_id] = "MENU"; await show_menu(context, update.effective_chat.id, update.effective_user)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); user_id = query.from_user.id
    try: await query.message.delete()
    except: pass
    if query.data == 'menu_send':
        keyboard = [[InlineKeyboardButton("BR - BlackRock 🏦", callback_data='grupo_BR'), InlineKeyboardButton("SF - Solflare ☀️", callback_data='grupo_SF')],[InlineKeyboardButton("BI - Binance 🟡", callback_data='grupo_BI')],[InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data='back_menu')]]
        await context.bot.send_message(query.message.chat_id, "📨 <b>Pilih Grup Untuk Laporan</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith('grupo_'):
        grupo = query.data.split('_')[1]; context.user_data['grupo'] = grupo; USER_STATE[user_id] = "KIRIM_REPORT"
        await context.bot.send_message(query.message.chat_id, f"✅ Grup: <b>{grupo}</b>\n\n📤 Kirim username/link Telegram yang mau direport:", parse_mode='HTML')
    elif query.data == 'add_sender':
        USER_STATE[user_id] = "ADD_EMAIL"; await context.bot.send_message(query.message.chat_id, "📧 <b>Langkah 1/2</b>\n\nKirim Email kamu dulu:", parse_mode='HTML')
    elif query.data == 'my_senders':
        config = load_config()
        if not config["senders"]: text = "📋 Kamu belum punya Sender.\nKlik 'Tambah Sender'"
        else: text = "📋 <b>Sender Saya:</b>\n\n" + "\n".join([f"• <code>{e}</code>" for e in config["senders"].keys()])
        await context.bot.send_message(query.message.chat_id, text, parse_mode='HTML')
    elif query.data == 'menu_status':
        now = datetime.datetime.now(TIMEZONE).strftime("%H:%M"); await context.bot.send_message(query.message.chat_id, f"📊 <b>Status Bot</b>\n\nVersi: {CURRENT_VERSION}\nJam: {now} WIB\nStatus: Online ✅", parse_mode='HTML')
    elif query.data == 'owner_panel' and user_id == DEVELOPER_ID:
        keyboard = [[InlineKeyboardButton("📷 Ganti Foto", callback_data='ganti_foto'), InlineKeyboardButton("🎵 Ganti Audio", callback_data='ganti_audio')],[InlineKeyboardButton("⬅️ Kembali", callback_data='back_menu')]]
        await context.bot.send_message(query.message.chat_id, "👑 <b>PANEL OWNER</b> ✨", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == 'ganti_foto' and user_id == DEVELOPER_ID:
        USER_STATE[user_id] = "GANTI_FOTO"; await context.bot.send_message(query.message.chat_id, "📷 Kirim foto baru:")
    elif query.data == 'ganti_audio' and user_id == DEVELOPER_ID:
        USER_STATE[user_id] = "GANTI_AUDIO"; await context.bot.send_message(query.message.chat_id, "🎵 Kirim audio baru:")
    elif query.data == 'back_menu':
        USER_STATE[user_id] = "MENU"; await show_menu(context, query.message.chat_id, query.from_user)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio))
    print(f"{BOT_NAME} {CURRENT_VERSION} Jalan..."); app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
