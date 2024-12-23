from typing import Optional, List
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update, delete

from .models import Base, User, UserProfile, Product, Cart

class Database:
    def __init__(self, database_url: str):
        self.database_url = f"sqlite+aiosqlite:///{database_url}"
        self.engine = create_async_engine(
            self.database_url,
            echo=True,  # Логирование SQL запросов
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        """Инициализация базы данных"""
        async with self.engine.begin() as conn:
            # Создаем таблицы если их нет
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        """Получение сессии для работы с БД"""
        async with self.async_session() as session:
            return session

    async def add_user(self, user_id: int, username: str, first_name: str) -> bool:
        """Добавление нового пользователя"""
        try:
            async with self.async_session() as session:
                # Проверяем существование пользователя
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    # Обновляем существующего пользователя
                    existing_user.username = username
                    existing_user.first_name = first_name
                else:
                    # Создаем нового пользователя
                    user = User(
                        user_id=user_id,
                        username=username,
                        first_name=first_name
                    )
                    session.add(user)
                
                await session.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка при добавлении пользователя: {e}")
            return False

    async def get_user_profile(self, user_id: int) -> Optional[tuple]:
        """Получение профиля пользователя"""
        try:
            async with self.async_session() as session:
                # Составной запрос для получения данных из обеих таблиц
                stmt = select(User, UserProfile).join(
                    UserProfile, User.user_id == UserProfile.user_id, isouter=True
                ).where(User.user_id == user_id)
                
                result = await session.execute(stmt)
                row = result.first()
                
                if not row:
                    return None
                
                user, profile = row
                
                if not profile:
                    return None
                
                return (
                    user.user_id,
                    profile.name,
                    profile.phone_number,
                    profile.email,
                    profile.location_lat,
                    profile.location_lon,
                    profile.age,
                    profile.photo_id,
                    user.reg_date.isoformat() if user.reg_date else None,
                    user.username
                )
        except Exception as e:
            logging.error(f"Ошибка при получении профиля: {e}")
            return None

    async def update_user_field(self, user_id: int, field: str, value: any) -> bool:
        """Обновление поля в профиле пользователя"""
        try:
            async with self.async_session() as session:
                # Проверяем существование профиля
                stmt = select(UserProfile).where(UserProfile.user_id == user_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    logging.error(f"Профиль пользователя {user_id} не найден")
                    return False
                
                # Обновляем поле
                setattr(profile, field, value)
                await session.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка при обновлении поля {field}: {e}")
            return False

    async def register_user(self, user_id: int, name: str, phone: str, email: str,
                          location_lat: float, location_lon: float,
                          age: int, photo_id: str) -> bool:
        """Регистрация профиля пользователя"""
        try:
            async with self.async_session() as session:
                # Проверяем существование профиля
                stmt = select(UserProfile).where(UserProfile.user_id == user_id)
                result = await session.execute(stmt)
                existing_profile = result.scalar_one_or_none()
                
                if existing_profile:
                    # Обновляем существующий профиль
                    existing_profile.name = name
                    existing_profile.phone_number = phone
                    existing_profile.email = email
                    existing_profile.location_lat = location_lat
                    existing_profile.location_lon = location_lon
                    existing_profile.age = age
                    existing_profile.photo_id = photo_id
                else:
                    # Создаем новый профиль
                    profile = UserProfile(
                        user_id=user_id,
                        name=name,
                        phone_number=phone,
                        email=email,
                        location_lat=location_lat,
                        location_lon=location_lon,
                        age=age,
                        photo_id=photo_id
                    )
                    session.add(profile)
                
                await session.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка при регистрации пользователя: {e}")
            return False

    async def is_user_registered(self, user_id: int) -> bool:
        """Проверка регистрации пользователя"""
        try:
            async with self.async_session() as session:
                stmt = select(UserProfile).where(UserProfile.user_id == user_id)
                result = await session.execute(stmt)
                return bool(result.scalar_one_or_none())
        except Exception as e:
            logging.error(f"Ошибка при проверке регистрации: {e}")
            return False

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> bool:
        """Добавление товара в корзину"""
        try:
            async with self.async_session() as session:
                # Получаем товар для проверки доступного количества
                product = await session.get(Product, product_id)
                if not product:
                    logging.error(f"Товар {product_id} не найден")
                    return False
                
                # Проверяем, есть ли уже этот товар в корзине
                stmt = select(Cart).where(
                    Cart.user_id == user_id,
                    Cart.product_id == product_id
                )
                result = await session.execute(stmt)
                existing_cart_item = result.scalar_one_or_none()
                
                if existing_cart_item:
                    # Обновляем количество существующего товара
                    existing_cart_item.quantity = quantity
                    existing_cart_item.product = product
                    existing_cart_item.check_available_quantity()
                else:
                    # Создаем новый элемент корзины
                    cart_item = Cart(
                        user_id=user_id,
                        product_id=product_id,
                        quantity=quantity
                    )
                    cart_item.product = product
                    cart_item.check_available_quantity()
                    session.add(cart_item)
                
                await session.commit()
                return True
        except ValueError as e:
            logging.error(f"Ошибка валидации: {e}")
            return False
        except Exception as e:
            logging.error(f"Ошибка при добавлении в корзину: {e}")
            return False

    async def get_cart(self, user_id: int) -> List[tuple]:
        """Получение содержимого корзины пользователя"""
        try:
            async with self.async_session() as session:
                stmt = select(Product, Cart).join(
                    Cart, Product.product_id == Cart.product_id
                ).where(Cart.user_id == user_id)
                
                result = await session.execute(stmt)
                return [(product, cart_item.quantity) for product, cart_item in result]
        except Exception as e:
            logging.error(f"Ошибка при получении корзины: {e}")
            return []

    async def clear_cart(self, user_id: int) -> bool:
        """Очистка корзины пользователя"""
        try:
            async with self.async_session() as session:
                stmt = delete(Cart).where(Cart.user_id == user_id)
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка при очистке корзины: {e}")
            return False

    async def close(self):
        """Закрытие соединения с базой данных"""
        await self.engine.dispose()

    async def get_cart_item_quantity(self, user_id: int, product_id: int) -> int:
        """Получение количества товара в корзине пользователя"""
        try:
            async with self.async_session() as session:
                stmt = select(Cart.quantity).where(
                    Cart.user_id == user_id,
                    Cart.product_id == product_id
                )
                result = await session.execute(stmt)
                quantity = result.scalar_one_or_none()
                return quantity or 0
        except Exception as e:
            logging.error(f"Ошибка при получении количества товара в корзине: {e}")
            return 0

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID"""
        try:
            async with self.async_session() as session:
                stmt = select(Product).where(Product.product_id == product_id)
                result = await session.execute(stmt)
                product = result.scalar_one_or_none()
                return product
        except Exception as e:
            logging.error(f"Ошибка при получении товара: {e}")
            return None

    async def remove_from_cart(self, user_id: int, product_id: int) -> bool:
        """Удаление товара из корзины"""
        try:
            async with self.async_session() as session:
                stmt = delete(Cart).where(
                    Cart.user_id == user_id,
                    Cart.product_id == product_id
                )
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка при удалении товара из корзины: {e}")
            return False