import os
import asyncio
import logging
from threading import Thread

from flask import Flask, send_from_directory
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    Message,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

# Налаштування
PORT = int(os.environ.get("PORT", 5000))
TOKEN = "8220398599:AAH9PJwgnpRf_q-xY-Vq7puHgTwQYB0YG-c"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Перевірка папки сайту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR)


@app.route("/")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


def run_flask():
    # На хостингу потрібно слухати 0.0.0.0 і порт від Render
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
    )


async def start_handler(message: Message, web_app_url: str):
    user_name = message.from_user.first_name or "друже"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Відкрити каталог Drop.ua",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Мої замовлення",
                    callback_data="my_orders",
                )
            ],
        ]
    )

    await message.answer(
        f"Вітаю, {user_name}, у Drop.ua! 👋\n\n"
        "Стильний одяг та аксесуари.\n"
        "Натискай кнопку нижче, щоб відкрити каталог!",
        reply_markup=keyboard,
    )


async def orders_handler(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        "📦 Розділ «Мої замовлення»\n\n"
        "Перегляд замовлень поки що не підключений."
    )


async def main():
    if not TOKEN:
        raise RuntimeError("Не вказано токен бота!")

    if not os.path.isfile(os.path.join(STATIC_DIR, "index.html")):
        raise FileNotFoundError(
            f"Не знайдено файл {STATIC_DIR}/index.html"
        )

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Запуск сайту у фоновому потоці
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Отримуємо посилання на сайт: на Render воно прийде автоматично, 
    # а для локального запуск ставимо запасний варіант
    web_app_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not web_app_url:
        web_app_url = f"http://127.0.0.1:{PORT}"

    print(f"Сайт працює на порту: {PORT}")
    print(f"Telegram Mini App URL: {web_app_url}")

    # Реєстрація обробників
    async def start(message: Message):
        await start_handler(message, web_app_url)

    dp.message.register(start, Command("start"))
    dp.callback_query.register(
        orders_handler,
        lambda callback: callback.data == "my_orders",
    )

    print("Бот запущено!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот зупинений.")
