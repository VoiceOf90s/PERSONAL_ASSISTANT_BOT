import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Конфигурация бота с валидацией переменных окружения"""
    
    BOT_TOKEN: str
    OWM_KEY: Optional[str] = None
    ADMIN_ID: Optional[int] = None
    
    @classmethod
    def validate(cls) -> bool:
        """Валидирует обязательные переменные окружения"""
        errors = []
        
        # Обязательные переменные
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            errors.append("BOT_TOKEN не установлен")
        else:
            cls.BOT_TOKEN = bot_token
        
        # Опциональные переменные
        cls.OWM_KEY = os.getenv("OWM_KEY")
        if not cls.OWM_KEY:
            logging.warning("OWM_KEY не установлен - функция погоды будет недоступна")
        
        admin_id_str = os.getenv("ADMIN_ID")
        if admin_id_str:
            try:
                cls.ADMIN_ID = int(admin_id_str)
            except ValueError:
                logging.warning(f"Неверный формат ADMIN_ID: {admin_id_str}")
        else:
            logging.info("ADMIN_ID не установлен - админ-панель недоступна")
        
        if errors:
            for error in errors:
                logging.error(f"❌ {error}")
            return False
        
        logging.info("✅ Конфигурация загружена успешно")
        return True


