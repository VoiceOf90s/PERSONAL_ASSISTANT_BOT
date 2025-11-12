from aiogram import Router, types, F
from aiogram.filters import Command
from utils.db import get_all_users
from config import Config
import logging

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not Config.ADMIN_ID:
        logging.warning("ADMIN_ID не установлен")
        return
    if message.from_user.id != Config.ADMIN_ID:
        return
    count = len(get_all_users())
    await message.answer(f"📊 Админ-панель\nАктивных пользователей: {count}")