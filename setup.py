from setuptools import setup, find_packages

setup(
    name="sudo_telegram_market",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "aiogram>=3.0.0",
        "python-dotenv>=0.19.0",
        "SQLAlchemy>=2.0.0",
        "aiosqlite>=0.19.0",
        "alembic>=1.12.0",
        "asyncpg>=0.28.0",
        "aiohttp>=3.8.0",
        "typer[all]>=0.9.0"
    ],
) 