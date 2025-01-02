from dataclasses import dataclass
from os import getenv
from dotenv import load_dotenv
import logging
import re
import os
from decimal import Decimal

@dataclass
class Config:
    token: str
    admin_ids: list[int]
    database_path: str
    db_url: str
    super_admin_id: int
    
    # Stars конфигурация
    STARS_RATE: Decimal = Decimal('1.35')  # Курс конвертации: 1 Star = 1.35 рубля
    MIN_STARS_AMOUNT: int = 1  # Минимальная сумма для оплаты Stars


def load_config() -> Config:
    load_dotenv()
    
    # Получаем и проверяем обязательные переменные
    token = getenv('BOT_TOKEN')
    if not token:
        raise ValueError("BOT_TOKEN is required")
    
    database_path = getenv('DATABASE_PATH')
    if not database_path:
        raise ValueError("DATABASE_PATH is required")
    
    db_url = getenv('DB_URL')
    if not db_url:
        raise ValueError("DB_URL is required")
    
    # Обработка admin_ids
    admin_ids_str = getenv('ADMIN_IDS', '')
    try:
        if admin_ids_str:
            # Удаляем все лишние символы, оставляем только числа и запятые
            admin_ids_str = re.sub(r'[^\d,]', '', admin_ids_str)
            admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
        else:
            admin_ids = []
    except ValueError as e:
        logging.error(f"Error parsing ADMIN_IDS: {e}")
        admin_ids = []
    
    # Обработка super_admin_id
    super_admin_id_str = getenv('SUPER_ADMIN_ID', '0')
    try:
        super_admin_id = int(super_admin_id_str)
        if super_admin_id == 0:
            raise ValueError("SUPER_ADMIN_ID is required")
    except ValueError as e:
        logging.error(f"Error parsing SUPER_ADMIN_ID: {e}")
        raise ValueError("Invalid SUPER_ADMIN_ID format")
    
    # Добавляем super_admin_id в список admin_ids, если его там нет
    if super_admin_id not in admin_ids:
        admin_ids.append(super_admin_id)
    
    config = Config(
        token=token,
        admin_ids=admin_ids,
        database_path=database_path,
        db_url=db_url,
        super_admin_id=super_admin_id
    )
    
    return config

# Загружаем конфигурацию
try:
    config = load_config()
    DB_URL = config.db_url
    admin_ids = config.admin_ids
    super_admin_id = config.super_admin_id
except Exception as e:
    logging.error(f"Failed to load configuration: {e}")
    raise

# Добавьте ID канала для Stars
STARS_CHANNEL_ID = None  # Замените на ID вашего канала