import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
BOT_TOKEN = "8882339062:AAETNkeVDrFKTabriCasyit-H4_QMqX5dto"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регулярное выражение для поиска слова "дать" в разных формах
PATTERN = re.compile(r'дать|дай|дайте|дашь|дадим|дадите|даю|даем|дает|дают', re.IGNORECASE)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "👋 Привет! Я бот, который благодарит людей за щедрость!\n\n"
        "📌 Если вы ответите (сделаете реплай) на моё сообщение со словом 'дать',\n"
        "я отвечу вам 'Спасибо тебе'!\n\n"
        "🤖 Работаю в группах и личных сообщениях."
    )

@dp.message()
async def handle_message(message: Message):
    """Обработчик всех сообщений"""
    
    # Игнорируем сообщения от самого бота
    if message.from_user.id == bot.id:
        return
    
    # Проверяем, является ли сообщение ответом (реплаем)
    if message.reply_to_message:
        # Проверяем, что ответ был на сообщение бота
        if message.reply_to_message.from_user.id == bot.id:
            # Проверяем, есть ли в сообщении слово "дать"
            if message.text and PATTERN.search(message.text):
                # Отвечаем человеку, который написал сообщение
                try:
                    # Упоминаем пользователя и благодарим
                    user_mention = f"@{message.from_user.username}" if message.from_user.username else f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                    
                    await message.reply(
                        f"Спасибо тебе, {user_mention}! 🎉",
                        parse_mode=ParseMode.MARKDOWN,
                        disable_notification=False
                    )
                    
                    logging.info(f"Бот ответил пользователю {message.from_user.id} на сообщение: {message.text}")
                    
                except Exception as e:
                    logging.error(f"Ошибка при отправке ответа: {e}")
                    # Если не удалось отправить с упоминанием, отправляем простой текст
                    try:
                        await message.reply("Спасибо тебе! 🎉")
                    except:
                        pass

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Показать статистику работы бота"""
    await message.answer(
        "📊 Статистика бота:\n\n"
        "✅ Бот активен и отслеживает сообщения с ключевым словом 'дать'\n"
        "📝 Бот отвечает только на реплаи к своим сообщениям\n"
        "👥 Работает в группах и личных сообщениях"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь по боту"""
    await message.answer(
        "🤖 **Как работает бот:**\n\n"
        "1️⃣ Добавьте бота в группу\n"
        "2️⃣ Когда кто-то отвечает (делает реплай) на сообщение бота\n"
        "   и пишет слово 'дать' (в любой форме),\n"
        "   бот отвечает ему 'Спасибо тебе'\n\n"
        "📝 **Пример:**\n"
        "Бот: 'Привет!'\n"
        "Пользователь (реплай на сообщение бота): 'дать 100к'\n"
        "Бот: 'Спасибо тебе, @username! 🎉'\n\n"
        "❌ **НЕ реагирует на:**\n"
        "• Обычные сообщения с 'дать'\n"
        "• Ответы на сообщения других пользователей\n"
        "• Сообщения без слова 'дать'\n\n"
        "⚙️ **Команды:**\n"
        "/start - Приветствие\n"
        "/help - Эта справка\n"
        "/stats - Статистика"
    )

async def main():
    """Главная функция запуска бота"""
    logging.info("Бот запущен!")
    
    # Устанавливаем команды
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="help", description="Помощь по боту"),
        types.BotCommand(command="stats", description="Статистика")
    ])
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
