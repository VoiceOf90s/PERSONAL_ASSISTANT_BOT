from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from utils.db import add_reminder, get_active_reminders, del_reminder

router = Router()

class Remind(StatesGroup):
    text = State()
    time = State()

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_remind")]
    ])

@router.message(Command("remind"))
async def remind_start(message: Message, state: FSMContext):
    # Проверяем, нет ли уже активного состояния
    current_state = await state.get_state()
    if current_state:
        await message.answer("⚠️ У вас уже есть активная операция. Используйте /cancel для отмены.")
        return
    
    await state.set_state(Remind.text)
    await message.answer(
        "О чём вам напомнить?",
        reply_markup=get_cancel_keyboard()
    )

@router.message(Remind.text)
async def remind_text(message: Message, state: FSMContext):
    # Обработка команды отмены
    text = message.text.strip().lower()
    if text in ["отмена", "cancel", "/cancel"]:
        await state.clear()
        await message.answer("❌ Создание напоминания отменено.")
        return
    
    # Валидация длины текста
    text = message.text.strip()
    if len(text) > 500:
        await message.answer("❌ Текст слишком длинный (максимум 500 символов). Попробуйте снова:")
        return
    if not text:
        await message.answer("❌ Текст не может быть пустым. Попробуйте снова:")
        return
    
    await state.update_data(text=text)
    await state.set_state(Remind.time)
    await message.answer(
        "Когда? (дд.мм чч:мм)\nНапример: 25.12 15:30",
        reply_markup=get_cancel_keyboard()
    )

@router.message(Remind.time)
async def remind_time(message: Message, state: FSMContext):
    # Обработка команды отмены
    text = message.text.strip().lower()
    if text in ["отмена", "cancel", "/cancel"]:
        await state.clear()
        await message.answer("❌ Создание напоминания отменено.")
        return
    
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m %H:%M")
        now = datetime.utcnow()
        dt = dt.replace(year=now.year)
        # Если дата уже прошла в этом году, добавляем год
        if dt < now:
            dt = dt.replace(year=now.year + 1)
        data = await state.get_data()
        add_reminder(message.from_user.id, data["text"], dt)
        await message.answer("✅ Напоминание сохранено!")
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Используйте: дд.мм чч:мм\nНапример: 25.12 15:30",
            reply_markup=get_cancel_keyboard()
        )

@router.callback_query(F.data == "cancel_remind")
async def cancel_remind(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание напоминания отменено.")
    await callback.answer()

@router.message(Command("myreminders"))
async def myrem(message: Message):
    rows = get_active_reminders(message.from_user.id)
    if not rows:
        return await message.answer("📋 Нет активных напоминаний.")
    
    # Форматируем список напоминаний с датами
    text = "📋 <b>Ваши напоминания:</b>\n\n"
    buttons = []
    
    for rid, _, reminder_text, remind_at_str in rows:
        try:
            # Парсим дату из БД
            remind_dt = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M")
            # Форматируем для отображения
            date_str = remind_dt.strftime("%d.%m в %H:%M")
            # Обрезаем текст если длинный
            text_preview = reminder_text[:30] + "..." if len(reminder_text) > 30 else reminder_text
            text += f"🔔 <b>{date_str}</b>\n{text_preview}\n\n"
            buttons.append([
                InlineKeyboardButton(
                    text=f"❌ {reminder_text[:20]}{'...' if len(reminder_text) > 20 else ''}",
                    callback_data=f"del_{rid}"
                )
            ])
        except ValueError:
            # Если не удалось распарсить дату, показываем как есть
            text_preview = reminder_text[:30] + "..." if len(reminder_text) > 30 else reminder_text
            text += f"🔔 {remind_at_str}\n{text_preview}\n\n"
            buttons.append([
                InlineKeyboardButton(
                    text=f"❌ {reminder_text[:20]}{'...' if len(reminder_text) > 20 else ''}",
                    callback_data=f"del_{rid}"
                )
            ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("del_"))
async def del_rem(callback: CallbackQuery):
    rid = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    # Проверяем права доступа и удаляем
    if del_reminder(rid, user_id):
        await callback.answer("✅ Удалено")
        await callback.message.edit_text("✅ Напоминание удалено.")
    else:
        await callback.answer("❌ Напоминание не найдено или нет доступа", show_alert=True)