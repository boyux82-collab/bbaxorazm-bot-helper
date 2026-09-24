import sqlite3
import threading
from flask import Flask, jsonify
from flask_cors import CORS
import telebot
from telebot import types

# ---------------- SOZLAMALAR ----------------
# BotFather bergan bot tokeningizni shu yerga yozing:
TOKEN = "8995426563:AAHD2YnX65UOUnRroKWceGJgck-Dvo-TNtY"

# Netlify'dagi Mini App havolangiz:
WEB_APP_URL = "https://spontaneous-unicorn-0d2a5f.netlify.app"

# O'zingizning Telegram raqamli ID'ingiz (@userinfobot orqali bilib olishingiz mumkin):
ADMIN_ID = 206710278  # O'z ID raqamingizni yozing
# --------------------------------------------

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)  # Mini App (brauzer) saytidan ma'lumot olishga ruxsat


# --- 1. MA'LUMOTLAR BAZASI (SQLite) ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, first_name, username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Yangi odam bo'lsa qo'shadi, avval kirgan bo'lsa qayta qo'shmaydi (bitta odam takrorlanmaydi)
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, first_name, username) 
        VALUES (?, ?, ?)
    """, (user_id, first_name, username))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

init_db()


# --- 2. MINI APP UCHUN API (index.html shu yerdan sonni oladi) ---
@app.route('/api/stats', methods=['GET'])
def get_stats():
    count = get_users_count()
    return jsonify({
        "status": "ok",
        "users_count": count
    })


# --- 3. TELEGRAM BOT BUYRUQLARI ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""

    # Bazaga yozib qo'yish
    add_user(user_id, first_name, username)

    # Mini App tugmasi
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    web_app_btn = types.KeyboardButton(
        text="📂 OPEN",
        web_app=types.WebAppInfo(url=WEB_APP_URL)
    )
    markup.add(web_app_btn)

    matn = (
        f"👋 Assalomu alaykum! {first_name}!\n\n"
        f"BBA Xorazm viloyati yordamchi botiga xush kelibsiz!\n"
        
    )
    bot.send_message(message.chat.id, matn, reply_markup=markup)


# Faqat siz uchun bot ichida tezkor statistika buyrug'i
@bot.message_handler(commands=['stat', 'stats'])
def admin_stat(message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        bot.send_message(
            message.chat.id,
            f"📊 <b>Bot statistikasi:</b>\n\n"
            f"👥 Jami obunachilar: <b>{count} ta</b>",
            parse_mode="HTML"
        )


# --- 4. FLASK VA BOTNI BIRGA ISHGA TUSHIRISH ---
def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    # Flask alohida oqimda (thread) ishlaydi
    threading.Thread(target=run_flask, daemon=True).start()
    print("✅ Statistika API (port 5000) va Telegram bot ishga tushdi...")
    bot.infinity_polling()