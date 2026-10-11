import os
import threading
import telebot
import requests
from telebot import types
from flask import Flask

# =======================================================
# ВПИШИТЕ СВОИ ДАННЫЕ В КАВЫЧКАХ МЕЖДУ СТРОКАМИ НИЖЕ:
BOT_TOKEN = "8823585045:AAHOtJopnVB-WuRjbtcX2azQ8epWCWCTE8g"
ATERNOS_SESSION = "ftKabEtBIOhwlS67eKh0FC4c1HZ2fqiLcP5edWvFtopuMOpO67y3UvQH1wRX1GPU5WXOZwYkMoNQFKRs7PhOVewstKJ15P9AKjYP"

# БЕЛЫЙ СПИСОК (Впиши сюда твой Telegram ID без кавычек):
ALLOWED_USERS = [5158884571] 
# =======================================================

app = Flask(__name__)
@app.route('/')
def home(): return "Бот работает!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

bot = telebot.TeleBot(BOT_TOKEN)

def get_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = types.KeyboardButton("🚀 Запустить сервер")
    btn_status = types.KeyboardButton("📊 Статус сервера")
    btn_ip = types.KeyboardButton("🌐 IP Сервера")
    markup.add(btn_start, btn_status)
    markup.add(btn_ip)
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.from_user.id not in ALLOWED_USERS: return
    bot.send_message(message.chat.id, f"Привет! Бот переведен на работу по токену сессии. Жми кнопку:", reply_markup=get_keyboard())

@bot.message_handler(func=lambda m: m.text == "🌐 IP Сервера")
def send_ip(message):
    if message.from_user.id not in ALLOWED_USERS: return
    bot.send_message(message.chat.id, "🎮 **IP адрес сервера:** `onyxpirsta.aternos.me`")

@bot.message_handler(func=lambda m: m.text == "📊 Статус сервера")
def send_status(message):
    if message.from_user.id not in ALLOWED_USERS: return
    bot.send_message(message.chat.id, "📊 **Статус можно узнать в игре по IP:**\n`onyxpirsta.aternos.me`")

@bot.message_handler(func=lambda m: m.text == "🚀 Запустить сервер")
def start_server_logic(message):
    if message.from_user.id not in ALLOWED_USERS: return
    status = bot.send_message(message.chat.id, "⏳ Отправляю мгновенный сигнал на запуск...")
    
    try:
        cookies = {"ATERNOS_SESSION": ATERNOS_SESSION}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # Заходим на страницу сервера, чтобы взять внутренний токен страницы (SEC)
        main_page = requests.get("https://aternos.org", cookies=cookies, headers=headers).text
        
        if 'window.SEC = "' in main_page:
            sec_token = main_page.split('window.SEC = "')[1].split('"')[0]
            
            # Отправляем точный скрытый запрос на включение сервера
            start_url = f"https://aternos.org{sec_token}&headroom=0"
            requests.get(start_url, cookies=cookies, headers=headers)
            
            bot.edit_message_text("✅ Сигнал на включение успешно отправлен! Сервер включается, заходите в Minecraft через пару минут.", message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ Ошибка авторизации. Проверьте ключ ATERNOS_SESSION в коде — возможно, он скопирован не полностью или устарел.", message.chat.id, status.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка отправки запроса: {str(e)}", message.chat.id, status.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling()
