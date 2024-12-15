from dataclasses import dataclass
from os import getenv
from dotenv import load_dotenv

@dataclass
class Config:
    token: str
    admin_ids: list[int]
    database_path: str
    db_url: str

def load_config() -> Config:
    load_dotenv()

    return Config(
        token=getenv('BOT_TOKEN'),
        admin_ids=[int(admin_id) for admin_id in getenv('ADMIN_IDS').split(',')],
        database_path=getenv('DATABASE_PATH'),
        db_url=getenv('DB_URL')
    )

config = load_config()
DB_URL = config.db_url 