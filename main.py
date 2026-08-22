import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота и ID администратора
BOT_TOKEN = "8882339062:AAETNkeVDrFKTabriCasyit-H4_QMqX5dto"
ADMIN_ID = 6539341659  # Ваш ID

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь для хранения ID групп
group_ids = set()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "👋 Привет! Я бот для рассылки сообщений.\n\n"
        "📌 Я буду рассылать ваши сообщения во все группы, где я являюсь администратором.\n"
        "Просто отправьте мне сообщение в личные сообщения."
    )

@dp.message(Command("groups"))
async def cmd_groups(message: Message):
    """Показать список групп, где бот админ"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    if not group_ids:
        await message.answer("📭 Бот не состоит ни в одной группе как администратор.")
        return
    
    groups_list = []
    for group_id in group_ids:
        try:
            chat = await bot.get_chat(group_id)
            groups_list.append(f"• {chat.title} (ID: {group_id})")
        except:
            groups_list.append(f"• Группа (ID: {group_id})")
    
    await message.answer(
        f"📋 Список групп, где бот является администратором:\n\n" + "\n".join(groups_list)
    )

@dp.message()
async def handle_message(message: Message):
    """Обработчик всех сообщений от администратора"""
    # Проверяем, что сообщение от администратора и это личный чат
    if (message.from_user.id == ADMIN_ID and 
        message.chat.type == "private" and 
        message.text):
        
        # Получаем текст сообщения
        text = message.text
        
        # Отправляем уведомление о начале рассылки
        await message.answer(f"📨 Начинаю рассылку сообщения во {len(group_ids)} групп...")
        
        # Счетчики для статистики
        success_count = 0
        fail_count = 0
        
        # Рассылаем сообщение во все группы
        for group_id in group_ids:
            try:
                # Отправляем сообщение в группу
                await bot.send_message(
                    chat_id=group_id,
                    text=text,
                    parse_mode=ParseMode.HTML
                )
                success_count += 1
                await asyncio.sleep(0.5)  # Небольшая задержка, чтобы не превысить лимиты
            except Exception as e:
                fail_count += 1
                logging.error(f"Ошибка отправки в группу {group_id}: {e}")
        
        # Отправляем отчет администратору
        await message.answer(
            f"✅ Рассылка завершена!\n"
            f"📤 Успешно отправлено: {success_count}\n"
            f"❌ Ошибок: {fail_count}"
        )
    
    # Если сообщение от обычного пользователя
    elif message.chat.type == "private" and message.from_user.id != ADMIN_ID:
        await message.answer(
            "⛔ Извините, этот бот предназначен только для администратора.\n"
            "Если вы администратор, обратитесь к разработчику."
        )

@dp.my_chat_member()
async def my_chat_member_handler(update: types.ChatMemberUpdated):
    """Обработчик изменений статуса бота в чатах"""
    # Если бота добавили в группу как администратора
    if update.new_chat_member.status in ["administrator", "member"]:
        chat_id = update.chat.id
        chat_type = update.chat.type
        
        # Проверяем, что это группа или супергруппа
        if chat_type in ["group", "supergroup"]:
            try:
                # Проверяем, является ли бот администратором
                chat_member = await bot.get_chat_member(chat_id, bot.id)
                if chat_member.status == "administrator":
                    group_ids.add(chat_id)
                    logging.info(f"Бот добавлен как администратор в группу {chat_id}")
                    
                    # Отправляем уведомление администратору
                    await bot.send_message(
                        ADMIN_ID,
                        f"✅ Бот добавлен как администратор в группу!\n"
                        f"ID: {chat_id}\n"
                        f"Название: {update.chat.title or 'Без названия'}"
                    )
            except Exception as e:
                logging.error(f"Ошибка при проверке прав в группе {chat_id}: {e}")
    
    # Если бота удалили из группы
    elif update.old_chat_member.status in ["administrator", "member"]:
        chat_id = update.chat.id
        if chat_id in group_ids:
            group_ids.remove(chat_id)
            logging.info(f"Бот удален из группы {chat_id}")
            
            # Отправляем уведомление администратору
            await bot.send_message(
                ADMIN_ID,
                f"❌ Бот удален из группы!\n"
                f"ID: {chat_id}\n"
                f"Название: {update.chat.title or 'Без названия'}"
            )

@dp.message(Command("update_groups"))
async def cmd_update_groups(message: Message):
    """Обновить список групп, где бот админ"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return
    
    await message.answer("🔄 Обновляю список групп...")
    
    # Очищаем текущий список
    group_ids.clear()
    
    # Получаем все чаты, где бот участвует
    try:
        # Получаем обновления
        updates = await bot.get_updates()
        
        # Проверяем все чаты в которых бот является администратором
        # В реальности, бот автоматически получает обновления через my_chat_member
        # Эта команда нужна для ручного обновления
        
        # Просто отправляем сообщение с текущим списком
        if not group_ids:
            await message.answer("📭 Бот не состоит ни в одной группе как администратор.\n"
                               "Пожалуйста, добавьте бота в группы как администратора.")
        else:
            groups_list = []
            for group_id in group_ids:
                try:
                    chat = await bot.get_chat(group_id)
                    groups_list.append(f"• {chat.title} (ID: {group_id})")
                except:
                    groups_list.append(f"• Группа (ID: {group_id})")
            
            await message.answer(
                f"📋 Обновленный список групп:\n\n" + "\n".join(groups_list)
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении: {e}")

async def main():
    """Главная функция запуска бота"""
    # Запускаем бота
    logging.info("Бот запущен!")
    
    # Устанавливаем команды
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="groups", description="Показать список групп"),
        types.BotCommand(command="update_groups", description="Обновить список групп")
    ])
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
