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

# БЕЛЫЙ СПИСОК (Впишите сюда ID через запятую):
ALLOWED_USERS = [123456789]  # ЗАМЕНИТЕ 123456789 НА ВАШ НАСТОЯЩИЙ ID ТГ
# =======================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

bot = telebot.TeleBot(BOT_TOKEN)

def get_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = types.KeyboardButton("🚀 Запустить сервер")
    btn_status = types.KeyboardButton("📊 Статус сервера")
    markup.add(btn_start, btn_status)
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к управлению этим сервером.")
        return
        
    bot.send_message(
        message.chat.id, 
        f"Привет, {message.from_user.first_name}! Панель управления активирована. Используй кнопки ниже:", 
        reply_markup=get_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "📊 Статус сервера")
def check_server_status(message):
    if message.from_user.id not in ALLOWED_USERS:
        return

    status_msg = bot.send_message(message.chat.id, "🔍 Опрашиваю сервер Minecraft...")
    try:
        server = JavaServer.lookup(SERVER_IP)
        query = server.status()
        text = (
            f"🟢 **Сервер СЕЙЧАС РАБОТАЕТ!**\n\n"
            f"👥 Игроков онлайн: `{query.players.online}/{query.players.max}`\n"
            f"⚡ Пинг: `{round(query.latency)} мс`"
        )
        bot.edit_message_text(text, message.chat.id, status_msg.message_id, parse_mode="Markdown")
    except Exception:
        bot.edit_message_text("🔴 **Сервер сейчас ВЫКЛЮЧЕН.**\nВы можете запустить его кнопкой ниже.", message.chat.id, status_msg.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🚀 Запустить сервер")
def start_server_logic(message):
    if message.from_user.id not in ALLOWED_USERS:
        return

    status = bot.send_message(message.chat.id, "⏳ Открываю виртуальный браузер...")
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            stealth(page)
            
            bot.edit_message_text("🔄 Захожу на сайт Aternos...", message.chat.id, status.message_id)
            page.goto("https://aternos.org", timeout=60000)
            page.wait_for_timeout(5000)
            
            bot.edit_message_text("🔑 Ввожу логин и пароль...", message.chat.id, status.message_id)
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
                    bot.send_photo(message.chat.id, photo, caption="❌ Не нашёл поля для ввода:")
                bot.delete_message(message.chat.id, status.message_id)
                browser.close()
                return

            page.wait_for_timeout(5000)
            
            if "server" not in page.url:
                page.goto("https://aternos.org", timeout=60000)
            
            bot.edit_message_text("⚡ Ищу кнопку запуска сервера...", message.chat.id, status.message_id)
            page.wait_for_selector("#start", timeout=15000)
            
            start_btn = page.query_selector("#start")
            if start_btn:
                start_btn.click()
                page.wait_for_timeout(3000)
                bot.edit_message_text("✅ Сигнал на запуск успешно отправлен! Сервер включается. Проверяйте статус через кнопку.", message.chat.id, status.message_id)
            else:
                bot.edit_message_text("❌ Кнопка запуска не найдена.", message.chat.id, status.message_id)
            browser.close()
            
    except Exception as e:
        try:
            if browser:
                page.screenshot(path="error_screen.png")
                with open("error_screen.png", "rb") as photo:
                    bot.send_photo(message.chat.id, photo, caption=f"❌ Ошибка: {str(e)}")
        except:
            bot.edit_message_text(f"❌ Критическая ошибка: {str(e)}", message.chat.id, status.message_id)

def run_tg_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    import os
    if not os.path.exists("/opt/render/.cache/ms-playwright"):
        print("Установка виртуального браузера...")
        os.system("playwright install chromium")
        
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Бот успешно запущен в облаке Render!")
    run_tg_bot()
