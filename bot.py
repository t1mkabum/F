import os
import asyncio
from dotenv import load_dotenv # type: ignore
from aiogram import Bot, Dispatcher # type: ignore

from app.handlers import router  # Импортируем роутер с обработчиками

async def main():
    load_dotenv()
    bot = Bot(token=os.getenv('TG_TOKEN'))  # Берем токен из .env
    dp = Dispatcher()
    dp.include_router(router)  # Добавляем обработчики команд
    await dp.start_polling(bot)  # Запускаем бота

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
        