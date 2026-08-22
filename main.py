import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8882339062:AAETNkeVDrFKTabriCasyit-H4_QMqX5dto"  # Токен от @BotFather
YOUR_TELEGRAM_ID = 6539341659  # Ваш ID (можно получить у @userinfobot)
OFFLINE_MINUTES = 0.3           # Через сколько минут бездействия считать вас "не в сети"

# Храним время вашего последнего взаимодействия с ботом
last_activity = datetime.now()

# Инициализация
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# ===== ОБНОВЛЯЕМ ВРЕМЯ АКТИВНОСТИ =====
@dp.message()
async def track_user_activity(message: Message):
    """Обновляем время, когда вы пишете боту"""
    global last_activity
    
    # Если сообщение от вас — обновляем время
    if message.from_user.id == YOUR_TELEGRAM_ID:
        last_activity = datetime.now()
        # Можно добавить отладочный вывод
        print(f"✅ Ваша активность обновлена: {last_activity.strftime('%H:%M:%S')}")
    
    # Если сообщение от другого пользователя — проверяем ваш статус
    elif message.from_user.id != YOUR_TELEGRAM_ID and not message.from_user.is_bot:
        await handle_incoming_message(message)

# ===== ОБРАБОТКА СООБЩЕНИЙ ОТ ДРУГИХ ЛЮДЕЙ =====
async def handle_incoming_message(message: Message):
    """Обрабатываем сообщения от других пользователей"""
    global last_activity
    
    # Вычисляем, сколько прошло времени с вашей последней активности
    time_diff = datetime.now() - last_activity
    is_online = time_diff.total_seconds() < (OFFLINE_MINUTES * 60)
    
    # Проверяем, был ли уже автоответ в этом диалоге (чтобы не спамить)
    user_id = message.from_user.id
    # Используем FSM или просто словарь (для простоты покажу через переменную)
    # В реальном проекте лучше использовать FSM или базу данных
    
    if not is_online:
        await message.reply(
            "В данный момент я не являюсь в сети. Ожидайте, отвечу в течение 5-10 минут."
        )
        print(f"📩 Автоответ отправлен пользователю {user_id}")

# ===== КОМАНДА ДЛЯ ПРОВЕРКИ СТАТУСА =====
@dp.message(Command("status"))
async def show_status(message: Message):
    """Команда для проверки текущего статуса"""
    if message.from_user.id != YOUR_TELEGRAM_ID:
        await message.reply("❌ У вас нет доступа к этой команде.")
        return
    
    time_diff = datetime.now() - last_activity
    is_online = time_diff.total_seconds() < (OFFLINE_MINUTES * 60)
    status = "🟢 Онлайн" if is_online else "🔴 Офлайн"
    
    await message.reply(
        f"📊 Ваш статус: {status}\n"
        f"⏱ Последняя активность: {time_diff.seconds // 60} мин {time_diff.seconds % 60} сек назад\n"
        f"⏰ Порог офлайна: {OFFLINE_MINUTES} минут"
    )

# ===== ЗАПУСК =====
async def main():
    print("🤖 Бот запущен!")
    print(f"👤 Ваш ID: {YOUR_TELEGRAM_ID}")
    print(f"⏱ Порог офлайна: {OFFLINE_MINUTES} минут")
    print("📌 Для обновления активности просто напишите боту любое сообщение")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
