import telebot
from telebot import types
import sqlite3

TOKEN = "8586054284:AAHWYhtpDON2N5ZRteAHDboauN-mJdcSV58"
ADMINS = [7735152347, 5779754488]
CHANNELS = ["@zebra_kino"]

bot = telebot.TeleBot(TOKEN)

# ===== DATABASE =====
conn = sqlite3.connect("kino.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS movies(
    code TEXT PRIMARY KEY,
    name TEXT,
    file_id TEXT
)""")

conn.commit()

# ===== FUNKSIYALAR =====
def check_sub(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)

    if not check_sub(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        for ch in CHANNELS:
            markup.add(types.InlineKeyboardButton(
                "📢 Kanalga obuna bo‘lish",
                url=f"https://t.me/{ch[1:]}"
            ))
        bot.send_message(
            message.chat.id,
            "❗ Botdan foydalanish uchun kanalga obuna bo‘ling",
            reply_markup=markup
        )
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎬 Kino qidirish", "📝 Kino so‘rash")

    if message.from_user.id in ADMINS:
        markup.add("⚙ Admin panel")

    bot.send_message(
        message.chat.id,
        "🎥 Zebra Kino Botga xush kelibsiz!",
        reply_markup=markup
    )

# ===== TEXT HANDLER =====
@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_text(message):

    if message.text == "🎬 Kino qidirish":
        bot.send_message(message.chat.id, "🔎 Kino kodi yoki nomini yuboring:")
        return

    if message.text == "📝 Kino so‘rash":
        bot.send_message(message.chat.id, "Qaysi kinoni xohlaysiz?")
        bot.register_next_step_handler(message, send_request)
        return

    if message.text == "⚙ Admin panel" and message.from_user.id in ADMINS:
        admin_panel(message)
        return

    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "❗ Avval kanalga obuna bo‘ling")
        return

    cursor.execute("SELECT file_id FROM movies WHERE code=? OR name LIKE ?",
                   (message.text, f"%{message.text}%"))
    movie = cursor.fetchone()

    if movie:
        bot.send_video(message.chat.id, movie[0])
    else:
        bot.send_message(message.chat.id, "❌ Kino topilmadi")

# ===== SO‘ROV =====
def send_request(message):
    for admin in ADMINS:
        try:
            bot.send_message(
                admin,
                f"📩 Yangi so‘rov:\n"
                f"👤 @{message.from_user.username}\n"
                f"🎬 {message.text}"
            )
        except:
            pass

    bot.send_message(message.chat.id, "✅ So‘rovingiz yuborildi")

# ===== ADMIN PANEL =====
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Kino qo‘shish")
    markup.add("📊 Statistika")
    markup.add("📢 Reklama yuborish")
    markup.add("⬅ Orqaga")

    bot.send_message(message.chat.id, "⚙ Admin panel", reply_markup=markup)

# ===== KINO QO‘SHISH =====
@bot.message_handler(func=lambda m: m.text == "➕ Kino qo‘shish")
def add_movie_start(message):
    if message.from_user.id not in ADMINS:
        return
    bot.send_message(message.chat.id, "🎥 Kinoni video qilib yuboring")
    bot.register_next_step_handler(message, save_video)

def save_video(message):
    if message.content_type != "video":
        bot.send_message(message.chat.id, "❗ Video yuboring")
        return
    file_id = message.video.file_id
    bot.send_message(message.chat.id, "🔢 Kino kodini kiriting:")
    bot.register_next_step_handler(message, save_code, file_id)

def save_code(message, file_id):
    code = message.text
    bot.send_message(message.chat.id, "🎬 Kino nomini kiriting:")
    bot.register_next_step_handler(message, save_movie, code, file_id)

def save_movie(message, code, file_id):
    name = message.text
    cursor.execute("INSERT INTO movies VALUES(?,?,?)",
                   (code, name, file_id))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Kino saqlandi")

# ===== STATISTIKA =====
@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    if message.from_user.id not in ADMINS:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM movies")
    movies = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"👥 Foydalanuvchilar: {users}\n🎬 Kinolar: {movies}"
    )

# ===== REKLAMA =====
@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish")
def broadcast_start(message):
    if message.from_user.id not in ADMINS:
        return
    bot.send_message(message.chat.id, "✍ Reklama matnini yuboring:")
    bot.register_next_step_handler(message, broadcast)

def broadcast(message):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for user in users:
        try:
            bot.send_message(user[0], message.text)
        except:
            pass

    bot.send_message(message.chat.id, "✅ Reklama yuborildi")

bot.polling(none_stop=True)
