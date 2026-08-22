import asyncio
import logging
import re
import json
import random
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
BOT_TOKEN = "8882339062:AAETNkeVDrFKTabriCasyit-H4_QMqX5dto"
ADMIN_ID = 6539341659  # Ваш ID для уведомлений

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регулярное выражение для поиска слова "дать"
PATTERN = re.compile(r'дать|дай|дайте|дашь|дадим|дадите|даю|даем|дает|дают', re.IGNORECASE)

# Путь к файлу базы данных
DB_FILE = "bot_database.json"

# Глобальная переменная для хранения данных
db_data = {
    "groups": [],  # Список ID групп
    "is_sending": False,  # Флаг отправки
    "last_send": None,  # Время последней отправки
    "send_count": 0  # Счетчик отправок
}

def load_db():
    """Загрузка базы данных из JSON файла"""
    global db_data
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                db_data = json.load(f)
            logging.info("База данных загружена")
        except Exception as e:
            logging.error(f"Ошибка загрузки БД: {e}")
            save_db()
    else:
        save_db()
        logging.info("Создана новая база данных")

def save_db():
    """Сохранение базы данных в JSON файл"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
        logging.info("База данных сохранена")
    except Exception as e:
        logging.error(f"Ошибка сохранения БД: {e}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "👋 Привет! Я многофункциональный бот!\n\n"
        "📌 **Функции:**\n"
        "1️⃣ Отвечаю 'Спасибо тебе' на реплаи с 'дать'\n"
        "2️⃣ Автоматически отправляю промо-сообщения в группы\n\n"
        "⚙️ **Команды администратора:**\n"
        "/start - Это сообщение\n"
        "/add_group - Добавить текущую группу\n"
        "/remove_group - Удалить текущую группу\n"
        "/list_groups - Список групп\n"
        "/send_promo - Отправить промо сейчас\n"
        "/stats - Статистика"
    )

@dp.message(Command("add_group"))
async def cmd_add_group(message: Message):
    """Добавить группу в список для рассылки"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    chat_id = str(message.chat.id)
    
    # Проверяем, что это группа
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("❌ Эта команда работает только в группах!")
        return
    
    if chat_id not in db_data["groups"]:
        db_data["groups"].append(chat_id)
        save_db()
        await message.answer(f"✅ Группа добавлена в список!\nID: {chat_id}")
        logging.info(f"Группа {chat_id} добавлена в список")
    else:
        await message.answer("ℹ️ Эта группа уже в списке!")

@dp.message(Command("remove_group"))
async def cmd_remove_group(message: Message):
    """Удалить группу из списка"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    chat_id = str(message.chat.id)
    
    if chat_id in db_data["groups"]:
        db_data["groups"].remove(chat_id)
        save_db()
        await message.answer(f"✅ Группа удалена из списка!\nID: {chat_id}")
        logging.info(f"Группа {chat_id} удалена из списка")
    else:
        await message.answer("ℹ️ Эта группа не найдена в списке!")

@dp.message(Command("list_groups"))
async def cmd_list_groups(message: Message):
    """Показать список групп"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    if not db_data["groups"]:
        await message.answer("📭 Список групп пуст.")
        return
    
    groups_list = []
    for group_id in db_data["groups"]:
        try:
            chat = await bot.get_chat(int(group_id))
            groups_list.append(f"• {chat.title} (ID: {group_id})")
        except:
            groups_list.append(f"• Группа (ID: {group_id})")
    
    await message.answer(
        f"📋 Список групп ({len(groups_list)}):\n\n" + "\n".join(groups_list)
    )

@dp.message(Command("send_promo"))
async def cmd_send_promo(message: Message):
    """Принудительная отправка промо-сообщений"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    await message.answer("🚀 Начинаю отправку промо-сообщений...")
    await send_promo_series()
    await message.answer("✅ Промо-сообщения отправлены!")

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Показать статистику"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    last_send = db_data["last_send"] or "Никогда"
    await message.answer(
        f"📊 **Статистика бота:**\n\n"
        f"📌 Групп в списке: {len(db_data['groups'])}\n"
        f"📤 Всего отправок: {db_data['send_count']}\n"
        f"🕐 Последняя отправка: {last_send}\n"
        f"🔄 Статус: {'Отправка...' if db_data['is_sending'] else 'Ожидание'}"
    )

@dp.message()
async def handle_message(message: Message):
    """Обработчик всех сообщений"""
    
    # Игнорируем сообщения от самого бота
    if message.from_user.id == bot.id:
        return
    
    # Проверяем ответ на сообщение бота
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == bot.id:
            if message.text and PATTERN.search(message.text):
                try:
                    user_mention = f"@{message.from_user.username}" if message.from_user.username else f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                    
                    await message.reply(
                        f"Спасибо тебе, {user_mention}! 🎉",
                        parse_mode=ParseMode.MARKDOWN,
                        disable_notification=False
                    )
                    
                    logging.info(f"Бот ответил пользователю {message.from_user.id} на сообщение: {message.text}")
                    
                except Exception as e:
                    logging.error(f"Ошибка при отправке ответа: {e}")
                    try:
                        await message.reply("Спасибо тебе! 🎉")
                    except:
                        pass

async def send_promo_series():
    """Отправка серии промо-сообщений во все группы"""
    if not db_data["groups"]:
        logging.warning("Нет групп для отправки")
        return
    
    if db_data["is_sending"]:
        logging.warning("Уже идет отправка")
        return
    
    db_data["is_sending"] = True
    save_db()
    
    try:
        for group_id in db_data["groups"]:
            try:
                # Генерируем случайные числа
                num1 = random.randint(1000, 5000000)
                num2 = random.randint(1, 15)
                
                # Отправляем первое сообщение
                await bot.send_message(
                    chat_id=int(group_id),
                    text="создать промо"
                )
                await asyncio.sleep(1)  # Задержка 1 секунда
                
                # Отправляем второе сообщение
                await bot.send_message(
                    chat_id=int(group_id),
                    text=str(num1)
                )
                await asyncio.sleep(1)  # Задержка 1 секунда
                
                # Отправляем третье сообщение
                await bot.send_message(
                    chat_id=int(group_id),
                    text=str(num2)
                )
                
                logging.info(f"Промо-сообщения отправлены в группу {group_id}: {num1}, {num2}")
                
                # Небольшая задержка между группами
                await asyncio.sleep(2)
                
            except Exception as e:
                logging.error(f"Ошибка отправки в группу {group_id}: {e}")
        
        # Обновляем статистику
        db_data["last_send"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_data["send_count"] += 1
        save_db()
        
    finally:
        db_data["is_sending"] = False
        save_db()

async def random_send_scheduler():
    """Фоновая задача для случайной отправки промо"""
    while True:
        try:
            # Ждем от 30 минут до 2 часов
            wait_time = random.randint(1800, 7200)  # в секундах
            logging.info(f"Следующая отправка через {wait_time//60} минут")
            await asyncio.sleep(wait_time)
            
            # Отправляем промо
            await send_promo_series()
            
        except Exception as e:
            logging.error(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(60)  # При ошибке ждем минуту

@dp.my_chat_member()
async def my_chat_member_handler(update: types.ChatMemberUpdated):
    """Обработчик изменений статуса бота в чатах"""
    # Если бота добавили в группу
    if update.new_chat_member.status in ["administrator", "member"]:
        chat_id = str(update.chat.id)
        if update.chat.type in ["group", "supergroup"]:
            if chat_id not in db_data["groups"]:
                # Автоматически добавляем группу
                db_data["groups"].append(chat_id)
                save_db()
                logging.info(f"Бот добавлен в группу {chat_id}, группа автоматически добавлена в список")
                
                # Уведомляем администратора
                await bot.send_message(
                    ADMIN_ID,
                    f"✅ Бот добавлен в новую группу!\n"
                    f"Название: {update.chat.title or 'Без названия'}\n"
                    f"ID: {chat_id}"
                )

async def main():
    """Главная функция запуска бота"""
    # Загружаем базу данных
    load_db()
    
    logging.info("Бот запущен!")
    logging.info(f"Групп в списке: {len(db_data['groups'])}")
    
    # Устанавливаем команды
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="add_group", description="Добавить группу"),
        types.BotCommand(command="remove_group", description="Удалить группу"),
        types.BotCommand(command="list_groups", description="Список групп"),
        types.BotCommand(command="send_promo", description="Отправить промо сейчас"),
        types.BotCommand(command="stats", description="Статистика")
    ])
    
    # Запускаем планировщик в фоновом режиме
    asyncio.create_task(random_send_scheduler())
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
