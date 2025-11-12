from datetime import datetime
import logging
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from utils.db import get_active_reminders, del_reminder

async def check_reminders(bot):
    """Проверка и отправка напоминаний с улучшенной обработкой ошибок"""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    rows = get_active_reminders()
    for rid, user_id, text, dt_str in rows:
        # Отправляем напоминания, которые должны были сработать (<= now)
        # Это предотвращает пропуск напоминаний между проверками
        if dt_str <= now:
            try:
                await bot.send_message(user_id, f"🔔 {text}")
                del_reminder(rid)
                logging.debug(f"Напоминание {rid} отправлено пользователю {user_id}")
            except TelegramForbiddenError:
                # Пользователь заблокировал бота - удаляем напоминание
                logging.warning(f"Пользователь {user_id} заблокировал бота. Удаляем напоминание {rid}")
                del_reminder(rid)
            except TelegramBadRequest as e:
                # Некорректный запрос (например, неверный chat_id)
                logging.error(f"Ошибка отправки напоминания {rid} пользователю {user_id}: {e}")
                # Удаляем напоминание, так как оно не может быть доставлено
                del_reminder(rid)
            except Exception as e:
                # Другие ошибки (сеть, таймаут и т.д.) - не удаляем, попробуем позже
                logging.error(f"Временная ошибка отправки напоминания {rid} пользователю {user_id}: {e}")
                # Не удаляем напоминание, чтобы попробовать отправить позже