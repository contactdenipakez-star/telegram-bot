import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

BOT_TOKEN = os.getenv("8795032718:AAHFpfcK13QZ9CvvpT8cRMFmk8CPBc_GpK0")

PUBLIC_CHANNEL = "@jetrolet"
STAT_CHANNEL = "@jetpackz"
OWNER_USERNAME = "@burgaa"

BOT_NAME = "CEK ID"

# FOTO BRANDING LOKAL
BRANDING_PHOTO = "branding.jpg"

# ================= DATABASE =================

conn = sqlite3.connect("cekid.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS username_history (
    user_id INTEGER,
    old_username TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    total_users INTEGER,
    total_checks INTEGER
)
""")

cursor.execute("SELECT * FROM stats")
if not cursor.fetchone():
    cursor.execute("INSERT INTO stats VALUES (0,0)")
    conn.commit()

# ================= LANGUAGE SYSTEM =================

TEXT = {
    "id": {
        "welcome": "Selamat datang di CEK ID 🚀\n\nKirim /cek atau reply pesan untuk mulai.",
        "data": "📌 DATA PENGGUNA",
        "premium_yes": "Ya",
        "premium_no": "Tidak",
        "history_empty": "Belum ada riwayat username.",
        "history_title": "📜 RIWAYAT USERNAME",
    },
    "en": {
        "welcome": "Welcome to CEK ID 🚀\n\nSend /cek or reply a message to start.",
        "data": "📌 USER DATA",
        "premium_yes": "Yes",
        "premium_no": "No",
        "history_empty": "No username history yet.",
        "history_title": "📜 USERNAME HISTORY",
    }
}

def get_lang(user):
    if not user or not user.language_code:
        return "en"
    if user.language_code.startswith("id"):
        return "id"
    return "en"

# ================= SAVE USER =================

def save_user(user):
    cursor.execute("SELECT username FROM users WHERE user_id=?", (user.id,))
    result = cursor.fetchone()

    if result:
        old_username = result[0]
        if old_username != user.username:
            cursor.execute(
                "INSERT INTO username_history (user_id, old_username) VALUES (?,?)",
                (user.id, old_username)
            )
            cursor.execute(
                "UPDATE users SET username=?, first_name=? WHERE user_id=?",
                (user.username, user.first_name, user.id)
            )
    else:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?,?,?)",
            (user.id, user.username, user.first_name)
        )
        cursor.execute("UPDATE stats SET total_users = total_users + 1")

    conn.commit()

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user)
    t = TEXT[lang]

    keyboard = [
        [InlineKeyboardButton("⭐Sell tg number⭐", url=f"https://t.me/{PUBLIC_CHANNEL.replace('@','')}")],
        [InlineKeyboardButton("👑Owner Bot👑", url=f"https://t.me/{OWNER_USERNAME}")]
    ]

    await update.message.reply_text(
        t["welcome"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= CEK =================

async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    save_user(user)

    lang = get_lang(user)
    t = TEXT[lang]

    target = user

    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user

    if update.message.forward_from:
        target = update.message.forward_from

    now = datetime.now()
    tanggal = now.strftime("%d-%m-%Y")
    waktu = now.strftime("%H:%M:%S")

    bahasa_user = target.language_code if target.language_code else "Unknown"

    text = (
        f"{t['data']}\n\n"
        f"👤 Nama       : {target.first_name}\n"
        f"🔗 Username   : @{target.username if target.username else '-'}\n"
        f"🆔 User ID    : {target.id}\n"
        f"⭐ Premium     : {t['premium_yes'] if target.is_premium else t['premium_no']}\n"
        f"🌍 Language    : {bahasa_user}\n"
        f"📅 Tanggal     : {tanggal}\n"
        f"⏰ Waktu       : {waktu}"
    )

    # Kirim foto branding lokal
    with open(BRANDING_PHOTO, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=text
        )

    # Update statistik
    cursor.execute("UPDATE stats SET total_checks = total_checks + 1")
    conn.commit()

    cursor.execute("SELECT total_users, total_checks FROM stats")
    total_users, total_checks = cursor.fetchone()

    stat_text = (
        f"📊 STATISTIK CEK ID\n\n"
        f"Nama: {target.first_name}\n"
        f"Username: @{target.username if target.username else '-'}\n"
        f"User ID: {target.id}\n"
        f"Tanggal: {tanggal} {waktu}\n\n"
        f"Total Users: {total_users}\n"
        f"Total Checks: {total_checks}"
    )

    await context.bot.send_message(chat_id=STAT_CHANNEL, text=stat_text)

# ================= HISTORY =================

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user)
    t = TEXT[lang]

    cursor.execute(
        "SELECT old_username FROM username_history WHERE user_id=?",
        (user.id,)
    )
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text(t["history_empty"])
        return

    text = f"{t['history_title']}\n\n"
    for row in rows:
        text += f"- @{row[0]}\n"

    await update.message.reply_text(text)

# ================= RUN =================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN belum di set di Railway.")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("cek", cek))
app.add_handler(CommandHandler("history", history))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cek))

print("CEK ID is running...")
app.run_polling()
