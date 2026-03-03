import os
import sqlite3
import datetime
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "7969351825:AAEKOTBeLjHdkHf6gHhIcoOde6Wp9m4SncI"
OWNER_USERNAME = "@burgaa"

# ================= DATABASE =================
conn = sqlite3.connect("burga_database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_seen TEXT,
    trust_score INTEGER DEFAULT 100,
    reports INTEGER DEFAULT 0
)
""")
conn.commit()

# ================= RANK SYSTEM =================
def get_rank(user_id):
    if user_id < 100000000:
        return "👑 BURGA ELITE"
    elif user_id < 500000000:
        return "💎 BURGA VIP"
    else:
        return "🛡 BURGA MEMBER"

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, first_seen) VALUES (?, ?)", (user.id, now))
        conn.commit()

    keyboard = [
        [InlineKeyboardButton("🔍 Check My ID", callback_data="check")],
        [InlineKeyboardButton("🪪 Generate ID Card", callback_data="card")],
        [InlineKeyboardButton("📞 Contact Owner", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        "💎 CEK ID KEREN BOT\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Secure • Premium • Trusted\n\n"
        "Click menu below to continue.",
        reply_markup=reply_markup
    )

# ================= BUTTON =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    cursor.execute("SELECT first_seen, trust_score, reports FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()

    first_seen = data[0]
    trust_score = data[1]
    reports = data[2]

    dc_id = abs(user.id) % 5 + 1
    rank = get_rank(user.id)
    premium = "YES 💎" if user.is_premium else "NO"

    if query.data == "check":
        await query.edit_message_text(
            f"💎 CEK ID KEREN\n\n"
            f"👤 Name: {user.first_name}\n"
            f"🔹 Username: @{user.username}\n"
            f"🆔 User ID: {user.id}\n"
            f"💎 Premium: {premium}\n"
            f"🌍 DC: {dc_id}\n"
            f"📅 First Seen: {first_seen}\n"
            f"🏆 Rank: {rank}\n"
            f"🛡 Trust Score: {trust_score}\n"
            f"🚨 Reports: {reports}\n\n"
            f"Owner: {OWNER_USERNAME}"
        )

    elif query.data == "card":
        await generate_card(query, user, first_seen, trust_score, reports, dc_id, rank, premium)

# ================= GENERATE CARD =================
async def generate_card(query, user, first_seen, trust_score, reports, dc_id, rank, premium):

    width, height = 900, 500
    img = Image.new("RGB", (width, height), "#111827")
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("arial.ttf", 50)
        font_small = ImageFont.truetype("arial.ttf", 28)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Ambil foto profil
    if user.photo:
        photos = await context.bot.get_user_profile_photos(user.id)

if photos.total_count > 0:
    file = await photos.photos[0][0].get_file()
    photo_bytes = await file.download_as_bytearray()

    from io import BytesIO
    from PIL import Image

    profile_photo = Image.open(BytesIO(photo_bytes))
else:
    profile_photo = None

        draw.text((350, 60), "CEK ID KEREN", fill="white", font=font_big)
        draw.text((350, 150), f"Name: {user.first_name}", fill="white", font=font_small)
        draw.text((350, 190), f"Username: @{user.username}", fill="white", font=font_small)
        draw.text((350, 230), f"User ID: {user.id}", fill="white", font=font_small)
        draw.text((350, 270), f"Premium: {user.is_premium}", fill="white", font=font_small)
        draw.text((350, 310), f"DC: {dc_id}", fill="white", font=font_small)
        draw.text((350, 350), f"Rank: {rank}", fill="white", font=font_small)

        draw.text((50, 460), "Powered by Burga", fill="white", font=font_small)

        bio = BytesIO()
        bio.name = "burga_card.png"
        img.save(bio, "PNG")
        bio.seek(0)

        await query.message.reply_photo(photo=bio, caption="💎 BURGA PREMIUM ID CARD")

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("BURGA OFFICIAL BOT RUNNING...")
app.run_polling()
