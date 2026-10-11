import os
import threading
import telebot
from telebot import types
from playwright.sync_api import sync_playwright
from flask import Flask

# =======================================================
# ВПИШИТЕ СВОИ ДАННЫЕ В КАВЫЧКАХ МЕЖДУ СТРОКАМИ НИЖЕ:
BOT_TOKEN = "8823585045:AAFg639ykUUtf4c1ofq4Qzh_5qykEyMxxE8"
ATERNOS_USER = "onyxpirsta"
ATERNOS_PASS = "Arsenijs_2024"
# =======================================================

# 1. Создаем обманный веб-сайт, чтобы тариф был бесплатным
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Основная логика Telegram-бота
bot = telebot.TeleBot(BOT_TOKEN)

def get_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚀 Запустить сервер"))
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id, 
        f"Привет, {message.from_user.first_name}! Я круглосуточный бот сервера. Нажми кнопку ниже, чтобы запустить игру.", 
        reply_markup=get_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "🚀 Запустить сервер")
def start_server_logic(message):
    status = bot.send_message(message.chat.id, "⏳ Открываю виртуальный браузер...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()
            
            bot.edit_message_text("🔄 Захожу на сайт Aternos...", message.chat.id, status.message_id)
            page.goto("https://aternos.org", wait_until="networkidle")
            
            page.fill("input[placeholder='Username']", ATERNOS_USER)
            page.fill("input[placeholder='Password']", ATERNOS_PASS)
            
            bot.edit_message_text("🔑 Авторизуюсь в системе...", message.chat.id, status.message_id)
            page.click("button:has-text('Login')")
            page.wait_for_timeout(5000)
            
            if "server" not in page.url:
                page.goto("https://aternos.org", wait_until="networkidle")
            
            bot.edit_message_text("⚡ Ищу кнопку запуска сервера...", message.chat.id, status.message_id)
            
            start_btn = page.query_selector("#start")
            if start_btn:
                start_btn.click()
                page.wait_for_timeout(5000)
                bot.edit_message_text("✅ Сигнал на запуск успешно отправлен! Сервер включается.", message.chat.id, status.message_id)
            else:
                bot.edit_message_text("❌ Кнопка запуска не найдена.", message.chat.id, status.message_id)
            browser.close()
    except Exception as e:
        bot.edit_message_text(f"❌ Произошла ошибка: {str(e)}", message.chat.id, status.message_id)

def run_tg_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Бот успешно запущен в облаке Render!")
    run_tg_bot()
