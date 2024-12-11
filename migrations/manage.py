import asyncio
import typer
from alembic.config import Config
from alembic import command

app = typer.Typer()

def get_alembic_config():
    """Получение конфигурации alembic"""
    config = Config("alembic.ini")
    return config

@app.command()
def init():
    """Инициализация миграций"""
    config = get_alembic_config()
    command.init(config, "migrations")

@app.command()
def migrate(message: str = typer.Option(..., "--message", "-m", help="Сообщение миграции")):
    """Создание новой миграции"""
    config = get_alembic_config()
    command.revision(config, message=message, autogenerate=True)

@app.command()
def upgrade(revision: str = "head"):
    """Обновление базы данных до указанной ревизии"""
    config = get_alembic_config()
    command.upgrade(config, revision)

@app.command()
def downgrade(revision: str = "-1"):
    """Откат базы данных до указанной ревизии"""
    config = get_alembic_config()
    command.downgrade(config, revision)

@app.command()
def history():
    """Просмотр истории миграций"""
    config = get_alembic_config()
    command.history(config)

if __name__ == "__main__":
    app() 