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
CURRENT_VERSION = "V7.8.2"

# LINK RAW GITHUB KAMU
URL_VERSION = "https://raw.githubusercontent.com/Araa546/main/version.txt"
URL_REPORT = "https://raw.githubusercontent.com/Araa546/main/report.py"

LOGIN, MT, EMAIL, PASSWORD, ADD_EMAIL, GANTI_FOTO, GANTI_AUDIO = range(7)

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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan.")
    context.user_data.clear()
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if update.effective_user.id in config.get("banned", []):
        await update.message.reply_text("🚫 Você foi banido.")
        return ConversationHandler.END
    latest = check_update()
    if latest and update.effective_user.id == DEVELOPER_ID:
        await update.message.reply_text(f"🆕 Update tersedia: {latest}\nKetik /update untuk update otomatis")
    await update.message.reply_text(f"🔒 <b>{BOT_NAME} {CURRENT_VERSION}</b>\n\nEste Bot é Privado\nDigite a Senha untuk continuar:", parse_mode='HTML')
    return LOGIN

async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= DEVELOPER_ID:
        await update.message.reply_text("❌ Hanya owner")
        return
    await update.message.reply_text("⏳ Download update dari github...")
    try:
        r = requests.get(URL_REPORT)
        with open("report.py", "w", encoding="utf-8") as f:
            f.write(r.text)
        await update.message.reply_text("✅ Update selesai! Restart bot...")
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal update: {e}")

async def login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if hash_password(update.message.text) == config["bot_password_hash"]:
        await show_menu(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Senha incorreta!")
        return LOGIN

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    keyboard = [
        [InlineKeyboardButton(f"{premium_emoji('🎯')} HANANIA REPORT", callback_data='report')],
        [
            InlineKeyboardButton(f"{premium_emoji('📮')} Sender", callback_data='sender_menu'),
            InlineKeyboardButton(f"{premium_emoji('📷')} Kirim Foto", callback_data='kirim_foto')
        ],
        [
            InlineKeyboardButton(f"{premium_emoji('🖼️')} Ganti Foto", callback_data='ganti_foto'),
            InlineKeyboardButton(f"{premium_emoji('🎵')} Ganti Audio", callback_data='ganti_audio')
        ],
        [
            InlineKeyboardButton(f"{premium_emoji('🔑')} Ganti Pass", callback_data='ganti_pass'),
            InlineKeyboardButton(f"{premium_emoji('ℹ️')} Info", callback_data='info')
        ],
        [InlineKeyboardButton(f"{premium_emoji('👑')} OWNER PANEL", callback_data='owner_panel')]
    ]
    caption = f"""<b>┏━━━━━━━ {BOT_NAME} {CURRENT_VERSION} ━━━━━━━┓</b>
<b>│</b> 👋 Olá <b>{update.effective_user.first_name}</b>
<b>│</b> Selamat datang di Panel Utama
<b>┗━━━━━━━━━━━━━━━┛</b>

Pilih menu dibawah untuk mulai 👇"""
    chat_id = update.effective_chat.id
    try:
        await context.bot.send_photo(chat_id=chat_id, photo=config["foto_url"], caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=caption + f"\n\n⚠️ Foto gagal dimuat\nError: {e}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    try:
        await context.bot.send_audio(chat_id=chat_id, audio=config["audio_url"])
    except:
        pass

async def owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if update.effective_user.id!= DEVELOPER_ID:
        await update.callback_query.answer("❌ Akses Ditolak!", show_alert=True)
        return
    total_sender = sum(len(v) for v in config['senders'].values())
    latest = check_update()
    update_btn = [InlineKeyboardButton("🆕 Update Bot", callback_data='do_update')] if latest else []
    text = f"""<b>{premium_emoji('👑')} OWNER PANEL</b>

<b>📊 Statistik:</b>
Versi: {config['version']}
Total Sender: {total_sender}
Total User: {len(config['senders'])}

<b>🖼️ Foto:</b> <code>{config['foto_url']}</code>
<b>🎵 Audio:</b> <code>{config['audio_url']}</code>"""
    keyboard = [update_btn, [InlineKeyboardButton("🔙 Kembali", callback_data='back')]]
    await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def do_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update_bot(update, context)

async def sender_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    senders = get_user_senders(config, update.effective_user.id)
    text = "<b>📮 DAFTAR SENDER KAMU</b>\n\n"
    text += "\n".join([f"• <code>{s}</code>" for s in senders]) if senders else "Belum ada sender. Klik 'Tambah Email'"
    keyboard = [[InlineKeyboardButton("➕ Tambah Email", callback_data='add_email')], [InlineKeyboardButton("🔙 Kembali", callback_data='back')]]
    await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def add_email_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📧 Kirim email Gmail yg mau didaftarin:")
    return ADD_EMAIL

async def add_email_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    config = load_config()
    senders = get_user_senders(config, update.effective_user.id)
    if email in senders:
        await update.message.reply_text("⚠️ Email sudah terdaftar.")
    else:
        senders.append(email)
        save_config(config)
        await update.message.reply_text(f"✅ Email <code>{email}</code> ditambahkan", parse_mode='HTML')
    await show_menu(update, context)
    return ConversationHandler.END

async def ganti_foto_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("🖼️ Kirim foto baru:")
    return GANTI_FOTO

async def ganti_foto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()
    await update.message.reply_text("⏳ Upload ke catbox... Tunggu 5 detik")
    try:
        files = {'reqtype': (None, 'fileupload'), 'fileToUpload': ('image.jpg', file_bytes, 'image/jpeg')}
        r = requests.post('https://catbox.moe/user/api.php', files=files, timeout=20)
        if r.status_code == 200 and "catbox.moe" in r.text:
            config = load_config()
            config["foto_url"] = r.text.strip()
            save_config(config)
            await update.message.reply_text(f"✅ Foto berhasil diganti!\n\nLink baru:\n<code>{r.text}</code>", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Gagal upload ke catbox\nStatus: {r.status_code}\nRespon: {r.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error upload: {e}\n\nCoba lagi atau cek internet termux")
    await show_menu(update, context)
    return ConversationHandler.END

async def ganti_audio_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("🎵 Kirim file audio mp3 sebagai DOKUMEN:")
    return GANTI_AUDIO

async def ganti_audio_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("❌ Kirim berupa FILE/DOKUMEN mp3")
        return GANTI_AUDIO
    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    await update.message.reply_text("⏳ Upload ke catbox...")
    try:
        files = {'reqtype': (None, 'fileupload'), 'fileToUpload': ('audio.mp3', file_bytes, 'audio/mpeg')}
        r = requests.post('https://catbox.moe/user/api.php', files=files, timeout=20)
        if r.status_code == 200 and "catbox.moe" in r.text:
            config = load_config()
            config["audio_url"] = r.text.strip()
            save_config(config)
            await update.message.reply_text(f"✅ Audio berhasil diganti!\n\n<code>{r.text}</code>", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Gagal upload: {r.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    await show_menu(update, context)
    return ConversationHandler.END

async def kirim_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    try:
        await update.callback_query.message.reply_photo(photo=config["foto_url"], caption="📷 Foto Bot")
    except:
        await update.callback_query.message.reply_text("❌ Link foto mati. Silahkan ganti foto.")

async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("BR - BlackRock", callback_data='group_BR')],
        [InlineKeyboardButton("SF - Solflare", callback_data='group_SF')],
        [InlineKeyboardButton("BI - Binance", callback_data='group_BI')],
        [InlineKeyboardButton("🔙 Kembali", callback_data='back')]
    ]
    await update.callback_query.message.reply_text("<b>Pilih Target Report:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def pilih_grup_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target_group'] = update.callback_query.data.split('_')[1]
    await update.callback_query.message.reply_text("📝 Kirim username target. Contoh: @penipu123")
    return MT

async def mt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mt'] = update.message.text
    await update.message.reply_text("📧 Kirim email sender yang sudah terdaftar:")
    return EMAIL

async def email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text("🔑 Masukkan App Password Gmail 16 digit:")
    return PASSWORD

async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text
    data = context.user_data
    await update.message.reply_text(f"⏳ Mengirim report ke {data['target_group']}...")

    try:
        config = load_config()
        targets = config["groups"][data['target_group']]
        success_count = 0

        for target in targets:
            msg = MIMEMultipart()
            msg['From'] = data['email']
            msg['To'] = target['email']
            msg['Subject'] = target['subject']
            body = f"Report Account: {data['mt']}\nFrom: {data['email']}"
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(data['email'], data['password'])
            server.send_message(msg)
            server.quit()
            success_count += 1

        await update.message.reply_text(f"✅ Berhasil kirim {success_count} report ke {data['target_group']}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal: {e}")

    await show_menu(update, context)
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'report':
        await report_menu(update, context)
    elif query.data in ['group_BR', 'group_SF', 'group_BI']:
        return await pilih_grup_target(update, context)
    elif query.data == 'sender_menu':
        await sender_menu(update, context)
    elif query.data == 'add_email':
        return await add_email_start(update, context)
    elif query.data == 'ganti_foto':
        return await ganti_foto_start(update, context)
    elif query.data == 'ganti_audio':
        return await ganti_audio_start(update, context)
    elif query.data == 'kirim_foto':
        await kirim_foto(update, context)
    elif query.data == 'owner_panel':
        await owner_panel(update, context)
    elif query.data == 'do_update':
        await do_update(update, context)
    elif query.data == 'back':
        await show_menu(update, context)
    elif query.data == 'info':
        await query.message.reply_text(f"<b>{BOT_NAME}</b>\nVersi: {CURRENT_VERSION}\nDev: {DEVELOPER_NAME}", parse_mode='HTML')

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('update', update_bot))
    conv_login = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    conv_report = ConversationHandler(
        entry_points=[CallbackQueryHandler(report_menu, pattern='^report$')],
        states={
            MT: [MessageHandler(filters.TEXT & ~filters.COMMAND, mt_handler)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_handler)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler)],
            ADD_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_email_save)],
            GANTI_FOTO: [MessageHandler(filters.PHOTO, ganti_foto_save)],
            GANTI_AUDIO: [MessageHandler(filters.Document.AUDIO | filters.Document.MP3, ganti_audio_save)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True
    )
    app.add_handler(conv_login)
    app.add_handler(conv_report)
    app.add_handler(CallbackQueryHandler(button_handler))
    print(f"{BOT_NAME} {CURRENT_VERSION} Jalan...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
