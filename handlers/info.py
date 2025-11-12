from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from utils.api import fetch_weather, fetch_rate, fetch_cat
from utils.db import get_user

router = Router()

def get_weather_icon(description: str) -> str:
    """Получить иконку погоды по описанию"""
    desc_lower = description.lower()
    if any(word in desc_lower for word in ["ясно", "clear"]):
        return "☀️"
    elif any(word in desc_lower for word in ["облачно", "cloud"]):
        return "☁️"
    elif any(word in desc_lower for word in ["дождь", "rain"]):
        return "🌧️"
    elif any(word in desc_lower for word in ["снег", "snow"]):
        return "❄️"
    elif any(word in desc_lower for word in ["туман", "fog", "mist"]):
        return "🌫️"
    elif any(word in desc_lower for word in ["гроза", "thunder"]):
        return "⛈️"
    else:
        return "🌤️"

@router.message(Command("weather"))
async def weather(message: Message):
    city = message.text.partition(" ")[2] or None
    if not city:
        user = get_user(message.from_user.id)
        city = user and user[3]
    if not city:
        return await message.answer(
            "❌ Укажите город.\n\n"
            "Пример: <code>/weather Москва</code>\n"
            "Или установите город по умолчанию: /settings",
            parse_mode="HTML"
        )
    
    # Показываем индикатор загрузки
    loading_msg = await message.answer("⏳ Загружаю данные о погоде...")
    
    data = await fetch_weather(city)
    if not data:
        await loading_msg.edit_text("❌ Город не найден. Проверьте название и попробуйте снова.")
        return
    
    icon = get_weather_icon(data['desc'])
    temp = data['temp']
    desc = data['desc'].capitalize()
    wind = data['wind']
    humidity = data.get('humidity', 'N/A')
    
    weather_text = (
        f"{icon} <b>Погода в {city.title()}</b>\n\n"
        f"🌡️ Температура: <b>{temp:.1f}°C</b>\n"
        f"☁️ Описание: {desc}\n"
        f"💨 Ветер: {wind} м/с\n"
        f"💧 Влажность: {humidity}%"
    )
    
    await loading_msg.edit_text(weather_text, parse_mode="HTML")

@router.message(Command("currency"))
async def currency(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("USD-RUB", callback_data="pair_USD-RUB"),
         InlineKeyboardButton("EUR-RUB", callback_data="pair_EUR-RUB")],
        [InlineKeyboardButton("🇺🇸 USD-EUR", callback_data="pair_USD-EUR")]
    ])
    await message.answer("Выберите пару:", reply_markup=kb)

@router.callback_query(F.data.startswith("pair_"))
async def currency_result(callback: CallbackQuery):
    pair = callback.data.split("_")[1]
    
    # Показываем индикатор загрузки
    try:
        await callback.message.edit_text("⏳ Загружаю курс...")
    except Exception:
        pass  # Если сообщение уже изменено
    
    rate = await fetch_rate(pair)
    if rate:
        frm, to = pair.split("-")
        try:
            await callback.message.edit_text(
                f"💱 <b>Курс валют</b>\n\n"
                f"<b>{frm}</b> → <b>{to}</b>\n"
                f"<b>{rate:.2f}</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            # Если не удалось отредактировать (сообщение устарело), отправляем новое
            await callback.message.answer(
                f"💱 <b>{pair}</b> = <b>{rate:.2f}</b>",
                parse_mode="HTML"
            )
        await callback.answer()
    else:
        try:
            await callback.message.edit_text("❌ Ошибка получения курса. Попробуйте позже.")
        except Exception:
            await callback.message.answer("❌ Ошибка получения курса. Попробуйте позже.")
        await callback.answer("Ошибка", show_alert=True)

@router.message(Command("cat"))
async def cat(message: Message):
    url = await fetch_cat()
    if not url:
        await message.answer("❌ Не удалось загрузить кота. Попробуйте позже.")
        return
    await message.answer_photo(url)