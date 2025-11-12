from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.db import set_city

router = Router()

class CitySettings(StatesGroup):
    city = State()

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_city")]
    ])

@router.message(Command("settings"))
async def settings(message: Message, state: FSMContext):
    # Проверяем, нет ли уже активного состояния
    current_state = await state.get_state()
    if current_state:
        await message.answer("⚠️ У вас уже есть активная операция. Используйте /cancel для отмены.")
        return
    
    await state.set_state(CitySettings.city)
    await message.answer(
        "Отправьте название вашего города:",
        reply_markup=get_cancel_keyboard()
    )

@router.message(CitySettings.city)
async def save_city(message: Message, state: FSMContext):
    # Обработка команды отмены
    text = message.text.strip().lower()
    if text in ["отмена", "cancel", "/cancel"]:
        await state.clear()
        await message.answer("❌ Сохранение города отменено.")
        return
    
    city = message.text.strip()
    if not city:
        await message.answer(
            "❌ Город не может быть пустым. Попробуйте снова:",
            reply_markup=get_cancel_keyboard()
        )
        return
    if len(city) > 100:
        await message.answer(
            "❌ Название города слишком длинное. Попробуйте снова:",
            reply_markup=get_cancel_keyboard()
        )
        return
    set_city(message.from_user.id, city)
    await message.answer(f"✅ Город '{city}' сохранён!")
    await state.clear()

@router.callback_query(F.data == "cancel_city")
async def cancel_city(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Сохранение города отменено.")
    await callback.answer()