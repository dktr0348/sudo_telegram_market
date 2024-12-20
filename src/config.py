from dataclasses import dataclass
from os import getenv
from dotenv import load_dotenv
import logging
import re
import os

@dataclass
class Config:
    token: str
    admin_ids: list[int]
    database_path: str
    db_url: str
    super_admin_id: int

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
    # Удаляем все лишние символы, оставляем только числа и запятые
    admin_ids_str = re.sub(r'[^\d,]', '', admin_ids_str)
    
    try:
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
        if not admin_ids:
            raise ValueError("ADMIN_IDS list is empty")
    except ValueError as e:
        logging.error(f"Error parsing ADMIN_IDS: {e}")
        raise ValueError(f"Invalid ADMIN_IDS format: {admin_ids_str}")
    
    # Обработка super_admin_id
    super_admin_id_str = getenv('SUPER_ADMIN_ID', '0')
    # Удаляем все лишние символы, оставляем только числа
    super_admin_id_str = re.sub(r'[^\d]', '', super_admin_id_str)
    
    try:
        super_admin_id = int(super_admin_id_str)
        if super_admin_id == 0:
            raise ValueError("SUPER_ADMIN_ID is required")
    except ValueError as e:
        logging.error(f"Error parsing SUPER_ADMIN_ID: {e}")
        raise ValueError("Invalid SUPER_ADMIN_ID format")
    
    return Config(
        token=token,
        admin_ids=admin_ids,
        database_path=database_path,
        db_url=db_url,
        super_admin_id=super_admin_id
    )

# Загружаем конфигурацию
try:
    config = load_config()
    DB_URL = config.db_url
    admin_ids = config.admin_ids
    super_admin_id = config.super_admin_id
except Exception as e:
    logging.error(f"Failed to load configuration: {e}")
    raise

# Преобразуем строку с ID администраторов в список целых чисел
admin_ids_str = os.getenv('ADMIN_IDS', '').strip('[]').split(',')
admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str if admin_id.strip()]
# Добавляем super_admin_id в список администраторов, если его там нет
if super_admin_id not in admin_ids:
    admin_ids.append(super_admin_id)