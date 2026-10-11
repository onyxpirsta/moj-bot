import os
import threading
import telebot
from telebot import types
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth
from mcstatus import JavaServer
from flask import Flask

# =======================================================
# ВПИШИТЕ СВОИ ДАННЫЕ В КАВЫЧКАХ МЕЖДУ СТРОКАМИ НИЖЕ:
BOT_TOKEN = "8823585045:AAFIuXx6gsh2Vnqd-tWBC6h1HoDx9YqC75M"
ATERNOS_USER = "onyxpirsta"
ATERNOS_PASS = "Arsenijs_2024"
SERVER_IP = "onyxpirsta.aternos.me"

# БЕЛЫЙ СПИСОК (Впишите сюда ваш Telegram ID):
ALLOWED_USERS = [5158884571] 
# =======================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

bot = telebot.TeleBot(BOT_TOKEN)

# Новое меню с тремя кнопками
def get_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = types.KeyboardButton("🚀 Запустить сервер")
    btn_status = types.KeyboardButton("📊 Статус сервера")
    btn_ip = types.KeyboardButton("🌐 IP Сервера")
    markup.add(btn_start, btn_status)
    markup.add(btn_ip)  # Кнопка IP на отдельной строчке
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.send_message(message.chat.id, "❌ У вас нет доступа.")
        return
    bot.send_message(
        message.chat.id, 
        f"Привет, {message.from_user.first_name}! Используй кнопки ниже:", 
        reply_markup=get_keyboard()
    )

# КНОПКА УЗНАТЬ IP
@bot.message_handler(func=lambda m: m.text == "🌐 IP Сервера")
def send_server_ip(message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    text = (
        f"🎮 **Данные для подключения к серверу:**\n\n"
        f"📍 IP адрес: `onyxpirsta.aternos.me`"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📊 Статус сервера")
def check_server_status(message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    status_msg = bot.send_message(message.chat.id, "🔍 Опрашиваю сервер...")
    try:
        server = JavaServer.lookup(SERVER_IP)
        query = server.status()
        text = (
            f"🟢 **Сервер СЕЙЧАС РАБОТАЕТ!**\n\n"
            f"👥 Игроков онлайн: `{query.players.online}/{query.players.max}`\n"
            f"⚡ Пинг: `{round(query.latency)} мс`"
        )
        bot.edit_message_text(text, message.chat.id, status_msg.message_id, parse_mode="Markdown")
    except:
        bot.edit_message_text("🔴 **Сервер сейчас ВЫКЛЮЧЕН.**", message.chat.id, status_msg.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🚀 Запустить сервер")
def start_server_logic(message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    status = bot.send_message(message.chat.id, "⏳ Запускаю виртуальный браузер...")
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            stealth(page)
            
            bot.edit_message_text("🔄 Захожу на Aternos...", message.chat.id, status.message_id)
            page.goto("https://aternos.org", timeout=60000)
            page.wait_for_timeout(5000)
            
            bot.edit_message_text("🔑 Ввожу данные...", message.chat.id, status.message_id)
            user_input = page.query_selector("#user") or page.query_selector("input[type='text']")
            pass_input = page.query_selector("#password") or page.query_selector("input[type='password']")
            
            if user_input and pass_input:
                user_input.fill(ATERNOS_USER)
                pass_input.fill(ATERNOS_PASS)
                login_btn = page.query_selector(".btn-success") or page.query_selector("button")
                if login_btn:
                    login_btn.click()
                else:
                    page.click("text=Login")
            else:
                page.screenshot(path="error_screen.png")
                with open("error_screen.png", "rb") as photo:
                    bot.send_photo(message.chat.id, photo, caption="❌ Не нашёл поля ввода:")
                browser.close()
                return

            page.wait_for_timeout(5000)
            if "server" not in page.url:
                page.goto("https://aternos.org", timeout=60000)
            
            bot.edit_message_text("⚡ Ищу кнопку включения...", message.chat.id, status.message_id)
            page.wait_for_selector("#start", timeout=15000)
            
            start_btn = page.query_selector("#start")
            if start_btn:
                start_btn.click()
                page.wait_for_timeout(3000)
                bot.edit_message_text("✅ Сигнал отправлен! Сервер включается.", message.chat.id, status.message_id)
            else:
                bot.edit_message_text("❌ Кнопка запуска не найдена.", message.chat.id, status.message_id)
            browser.close()
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка браузера: {str(e)}", message.chat.id, status.message_id)

if __name__ == "__main__":
    if not os.path.exists("/opt/render/.cache/ms-playwright"):
        os.system("playwright install chromium")
    threading.Thread(target=run_web_server, daemon=True).start()
    run_tg_bot = lambda: bot.infinity_polling()
    run_tg_bot()
