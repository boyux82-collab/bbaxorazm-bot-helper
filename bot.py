import sqlite3
import threading
import urllib.parse
from flask import Flask, jsonify
from flask_cors import CORS
import telebot
from telebot import types

# ---------------- SOZLAMALAR ----------------
TOKEN = "8995426563:AAHD2YnX65UOUnRroKWceGJgck-Dvo-TNtY"
WEB_APP_URL = "https://boyux82-collab.github.io/bbaxorazm-bot-helper/"
ADMIN_ID = 206710278
# --------------------------------------------

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

# --- BAZA ---
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

# --- STATISTIKA API ---
@app.route('/api/stats', methods=['GET'])
def get_stats():
    count = get_users_count()
    return jsonify({
        "status": "ok",
        "users_count": count
    })

# --- /START BUYRUG'I ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = message.from_user.username or ""

    add_user(user_id, first_name, username)

    # Ismni to'g'ridan-to'g'ri havolaga xavfsiz ulaymiz
    encoded_name = urllib.parse.quote(first_name)
    user_app_url = f"{WEB_APP_URL}?name={encoded_name}"

    markup = types.InlineKeyboardMarkup()
    web_app_btn = types.InlineKeyboardButton(
        text="✨ Ilovani ochish",
        web_app=types.WebAppInfo(url=user_app_url)
    )
    markup.add(web_app_btn)

    matn = (
        f"👋 Assalomu alaykum, {first_name}!\n\n"
        f"Yordamchi botiga xush kelibsiz! ✨\n"
    )
    bot.send_message(message.chat.id, matn, reply_markup=markup)

@bot.message_handler(commands=['stat', 'stats'])
def admin_stat(message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        bot.send_message(message.chat.id, f"👥 Jami obunachilar: <b>{count} ta</b>", parse_mode="HTML")

def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()