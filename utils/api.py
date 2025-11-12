import os
import aiohttp
import logging
import time
from typing import Optional, Dict, Any
from config import Config

# Кэш для API запросов
_cache: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = {
    'weather': 600,  # 10 минут
    'rate': 300,    # 5 минут
    'cat': 60       # 1 минута
}

async def fetch_weather(city: str) -> Optional[Dict[str, Any]]:
    """Получить погоду для города с кэшированием"""
    if not Config.OWM_KEY:
        logging.error("OWM_KEY не установлен")
        return None
    
    # Проверка кэша
    cache_key = f"weather:{city.lower()}"
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if time.time() - timestamp < CACHE_TTL['weather']:
            logging.debug(f"Использован кэш для погоды: {city}")
            return data
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={Config.OWM_KEY}&units=metric&lang=ru"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                result = dict(
                    temp=data["main"]["temp"],
                    desc=data["weather"][0]["description"],
                    wind=data["wind"]["speed"],
                    humidity=data["main"]["humidity"]
                )
                # Сохраняем в кэш
                _cache[cache_key] = (result, time.time())
                return result
    except (aiohttp.ClientError, KeyError, ValueError) as e:
        logging.error(f"Ошибка получения погоды для {city}: {e}")
        return None

async def fetch_rate(pair: str) -> Optional[float]:
    """Получить курс валют с кэшированием"""
    # Проверка кэша
    cache_key = f"rate:{pair}"
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if time.time() - timestamp < CACHE_TTL['rate']:
            logging.debug(f"Использован кэш для курса: {pair}")
            return data
    
    try:
        frm, to = pair.split("-")
        url = f"https://api.exchangerate.host/convert?from={frm}&to={to}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                result = data.get("result")
                if result:
                    # Сохраняем в кэш
                    _cache[cache_key] = (result, time.time())
                return result
    except (aiohttp.ClientError, ValueError, KeyError) as e:
        logging.error(f"Ошибка получения курса {pair}: {e}")
        return None

async def fetch_cat() -> Optional[str]:
    """Получить случайное фото кота с кэшированием"""
    # Проверка кэша (короткий TTL, так как нужны разные коты)
    cache_key = "cat:latest"
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if time.time() - timestamp < CACHE_TTL['cat']:
            logging.debug("Использован кэш для кота")
            return data
    
    url = "https://api.thecatapi.com/v1/images/search"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                if not data or len(data) == 0:
                    return None
                result = data[0].get("url")
                if result:
                    # Сохраняем в кэш
                    _cache[cache_key] = (result, time.time())
                return result
    except (aiohttp.ClientError, KeyError, IndexError) as e:
        logging.error(f"Ошибка получения кота: {e}")
        return None