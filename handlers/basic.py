from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.db import save_user, get_user, get_active_reminders

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user = message.from_user
    save_user(user.id, user.username, user.full_name)
    user_data = get_user(user.id)
    if user_data and user_data[3]:  # Проверяем наличие города
        await message.answer("👋 Снова здравствуйте!")
    else:
        await message.answer(f"👋 Привет, {user.full_name}!\n/help – список команд")

@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "📋 <b>Доступные команды:</b>\n\n"
        "🌤 /weather [город] – погода\n"
        "💱 /currency – курсы валют\n"
        "🐱 /cat – случайный кот\n"
        "🔔 /remind – создать напоминание\n"
        "📝 /myreminders – мои напоминания\n"
        "⚙️ /settings – город по умолчанию\n"
        "📊 /stats – статистика\n"
        "❌ /cancel – отменить текущую операцию",
        parse_mode="HTML"
    )

@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    """Универсальная команда для отмены FSM состояний"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активных операций для отмены.")
        return
    
    await state.clear()
    await message.answer("✅ Операция отменена.")

@router.message(Command("stats"))
async def stats_cmd(message: Message):
    """Статистика пользователя"""
    user_id = message.from_user.id
    user_data = get_user(user_id)
    reminders_count = len(get_active_reminders(user_id))
    
    city = user_data[3] if user_data and user_data[3] else "не установлен"
    
    await message.answer(
        f"📊 <b>Ваша статистика:</b>\n\n"
        f"🔔 Активных напоминаний: {reminders_count}\n"
        f"🌍 Город по умолчанию: {city}",
        parse_mode="HTML"
    )

@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    """Обработка неизвестных команд"""
    text = message.text.strip()
    # Команда не распознана другими обработчиками
    await message.answer(
        f"❓ Неизвестная команда: <code>{text}</code>\n\n"
        f"Используйте /help для списка доступных команд.",
        parse_mode="HTML"
    )