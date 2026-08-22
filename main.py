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

# Регулярные выражения
PATTERN_DAT = re.compile(r'дать|дай|дайте|дашь|дадим|дадите|даю|даем|дает|дают', re.IGNORECASE)
PATTERN_MONEY = re.compile(r'дай\s+нк|дай\s+денег|дайте\s+нк|дайте\s+денег', re.IGNORECASE)

# Путь к файлу базы данных
DB_FILE = "bot_database.json"

# Глобальная переменная для хранения данных
db_data = {
    "groups": [],  # Список ID групп
    "is_sending": False,  # Флаг отправки
    "last_send": None,  # Время последней отправки
    "send_count": 0,  # Счетчик отправок
    "user_requests": {}  # Словарь с временем запросов пользователей
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
        "2️⃣ Автоматически отправляю промо-сообщения в группы\n"
        "3️⃣ Выдаю деньги по запросу 'дай нк' или 'дай денег'\n\n"
        "⚙️ **Команды администратора:**\n"
        "/start - Это сообщение\n"
        "/add_group - Добавить текущую группу\n"
        "/remove_group - Удалить текущую группу\n"
        "/list_groups - Список групп\n"
        "/send_promo - Отправить промо сейчас\n"
        "/stats - Статистика\n"
        "/reset_user - Сбросить таймер пользователя (ID)"
    )

@dp.message(Command("add_group"))
async def cmd_add_group(message: Message):
    """Добавить группу в список для рассылки"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    chat_id = str(message.chat.id)
    
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
        f"🔄 Статус: {'Отправка...' if db_data['is_sending'] else 'Ожидание'}\n"
        f"👥 Пользователей в кэше: {len(db_data['user_requests'])}"
    )

@dp.message(Command("reset_user"))
async def cmd_reset_user(message: Message):
    """Сбросить таймер пользователя"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /reset_user [user_id]")
        return
    
    user_id = args[1]
    if user_id in db_data["user_requests"]:
        del db_data["user_requests"][user_id]
        save_db()
        await message.answer(f"✅ Таймер пользователя {user_id} сброшен!")
    else:
        await message.answer(f"ℹ️ Пользователь {user_id} не найден в кэше.")

async def check_money_request(user_id: int) -> tuple:
    """
    Проверяет, может ли пользователь запросить деньги
    Возвращает: (можно_ли, время_ожидания_в_секундах)
    """
    user_id_str = str(user_id)
    current_time = datetime.now()
    
    if user_id_str in db_data["user_requests"]:
        last_request_time = datetime.fromisoformat(db_data["user_requests"][user_id_str])
        time_diff = current_time - last_request_time
        
        if time_diff < timedelta(minutes=30):
            # Ждем 30 минут
            wait_seconds = int((timedelta(minutes=30) - time_diff).total_seconds())
            return False, wait_seconds
        else:
            # Прошло больше 30 минут, обновляем время
            db_data["user_requests"][user_id_str] = current_time.isoformat()
            save_db()
            return True, 0
    else:
        # Первый запрос
        db_data["user_requests"][user_id_str] = current_time.isoformat()
        save_db()
        return True, 0

@dp.message()
async def handle_message(message: Message):
    """Обработчик всех сообщений"""
    
    # Игнорируем сообщения от самого бота
    if message.from_user.id == bot.id:
        return
    
    # Проверяем ответ на сообщение бота
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == bot.id:
            if message.text:
                user_id = message.from_user.id
                user_mention = f"@{message.from_user.username}" if message.from_user.username else f"[{message.from_user.first_name}](tg://user?id={user_id})"
                
                # Проверка на "дай нк" или "дай денег"
                if PATTERN_MONEY.search(message.text):
                    can_request, wait_time = await check_money_request(user_id)
                    
                    if can_request:
                        # Генерируем случайное число
                        random_amount = random.randint(100000, 2500000)
                        await message.reply(
                            f"дать {random_amount:}"
                            parse_mode=ParseMode.MARKDOWN
                        )
                        logging.info(f"Выдано денег пользователю {user_id}: {random_amount}")
                    else:
                        # Ждем 30 минут
                        minutes = wait_time // 60
                        seconds = wait_time % 60
                        await message.reply(
                            f"⏳ Подождите еще {minutes} минут {seconds} секунд",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        logging.info(f"Пользователю {user_id} отказано в выдаче (ждать {wait_time}с)")
                
                # Проверка на обычное "дать" (без "нк" или "денег")
                elif PATTERN_DAT.search(message.text) and not PATTERN_MONEY.search(message.text):
                    try:
                        await message.reply(
                            f"Спасибо тебе, {user_mention}! 🎉",
                            parse_mode=ParseMode.MARKDOWN,
                            disable_notification=False
                        )
                        logging.info(f"Бот ответил пользователю {user_id} на сообщение: {message.text}")
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
                await asyncio.sleep(1)
                
                # Отправляем второе сообщение
                await bot.send_message(
                    chat_id=int(group_id),
                    text=str(num1)
                )
                await asyncio.sleep(1)
                
                # Отправляем третье сообщение
                await bot.send_message(
                    chat_id=int(group_id),
                    text=str(num2)
                )
                
                logging.info(f"Промо-сообщения отправлены в группу {group_id}: {num1}, {num2}")
                await asyncio.sleep(2)
                
            except Exception as e:
                logging.error(f"Ошибка отправки в группу {group_id}: {e}")
        
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
            wait_time = random.randint(1800, 7200)  # 30-120 минут
            logging.info(f"Следующая отправка через {wait_time//60} минут")
            await asyncio.sleep(wait_time)
            await send_promo_series()
        except Exception as e:
            logging.error(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(60)

@dp.my_chat_member()
async def my_chat_member_handler(update: types.ChatMemberUpdated):
    """Обработчик изменений статуса бота в чатах"""
    if update.new_chat_member.status in ["administrator", "member"]:
        chat_id = str(update.chat.id)
        if update.chat.type in ["group", "supergroup"]:
            if chat_id not in db_data["groups"]:
                db_data["groups"].append(chat_id)
                save_db()
                logging.info(f"Бот добавлен в группу {chat_id}, группа автоматически добавлена в список")
                
                await bot.send_message(
                    ADMIN_ID,
                    f"✅ Бот добавлен в новую группу!\n"
                    f"Название: {update.chat.title or 'Без названия'}\n"
                    f"ID: {chat_id}"
                )

async def main():
    """Главная функция запуска бота"""
    load_db()
    
    logging.info("Бот запущен!")
    logging.info(f"Групп в списке: {len(db_data['groups'])}")
    logging.info(f"Пользователей в кэше: {len(db_data['user_requests'])}")
    
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="add_group", description="Добавить группу"),
        types.BotCommand(command="remove_group", description="Удалить группу"),
        types.BotCommand(command="list_groups", description="Список групп"),
        types.BotCommand(command="send_promo", description="Отправить промо сейчас"),
        types.BotCommand(command="stats", description="Статистика"),
        types.BotCommand(command="reset_user", description="Сбросить таймер пользователя")
    ])
    
    asyncio.create_task(random_send_scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
