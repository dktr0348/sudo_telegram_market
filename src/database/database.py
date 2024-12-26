from typing import Optional, List
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update, delete, or_
from sqlalchemy.orm import joinedload

from .models import Base, User, UserProfile, Product, Cart, Order, OrderItem
from .models import DeliveryMethod, PaymentMethod, OrderStatus
from .models import Favorite, Review

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

    async def create_order(self, user_id: int, delivery_address: str, 
                          delivery_method: str, payment_method: str,
                          total_amount: float, items: list) -> Order:
        """Создание нового заказа"""
        try:
            async with self.async_session() as session:
                # Создаем заказ
                order = Order(
                    user_id=user_id,
                    delivery_address=delivery_address,
                    delivery_method=DeliveryMethod(delivery_method),
                    payment_method=PaymentMethod(payment_method),
                    total_amount=total_amount,
                    status=OrderStatus.NEW
                )
                session.add(order)
                await session.flush()
                
                # Добавляем товары заказа
                for product, quantity in items:
                    order_item = OrderItem(
                        order_id=order.order_id,
                        product_id=product.product_id,
                        quantity=quantity,
                        price=product.price
                    )
                    session.add(order_item)
                
                await session.commit()
                return order
        except Exception as e:
            logging.error(f"Ошибка при создании заказа: {e}")
            return None

    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Получение списка заказов пользователя"""
        try:
            async with self.async_session() as session:
                stmt = select(Order).where(Order.user_id == user_id)
                result = await session.execute(stmt)
                return result.scalars().all()
        except Exception as e:
            logging.error(f"Ошибка при получении заказов: {e}")
            return []

    async def update_order_status(self, order_id: int, new_status: OrderStatus) -> bool:
        """Обновление статуса заказа"""
        try:
            async with self.async_session() as session:
                stmt = select(Order).where(Order.order_id == order_id)
                result = await session.execute(stmt)
                order = result.scalar_one_or_none()
                
                if order:
                    order.status = new_status
                    await session.commit()
                    return True
                return False
        except Exception as e:
            logging.error(f"Ошибка при обновлении статуса заказа: {e}")
            return False

    async def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Получение заказа по ID"""
        try:
            async with self.async_session() as session:
                stmt = select(Order).options(
                    joinedload(Order.items).joinedload(OrderItem.product)
                ).where(Order.order_id == order_id)
                result = await session.execute(stmt)
                return result.unique().scalar_one_or_none()
        except Exception as e:
            logging.error(f"Ошибка при получении заказа: {e}")
            return None

    async def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Получение товаров заказа"""
        try:
            async with self.async_session() as session:
                stmt = select(OrderItem).options(
                    joinedload(OrderItem.product)
                ).where(OrderItem.order_id == order_id)
                result = await session.execute(stmt)
                return result.unique().scalars().all()
        except Exception as e:
            logging.error(f"Ошибка при получении товаров заказа: {e}")
            return []

    async def search_products(self, query: str) -> List[Product]:
        """Поиск товаров по названию или описанию"""
        try:
            async with self.async_session() as session:
                stmt = select(Product).where(
                    or_(
                        Product.name.ilike(f"%{query}%"),
                        Product.description.ilike(f"%{query}%")
                    )
                )
                result = await session.execute(stmt)
                return result.scalars().all()
        except Exception as e:
            logging.error(f"Ошибка при поиске товаров: {e}")
            return []

    async def get_products_filtered(
        self, 
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = 'name',
        sort_order: str = 'asc'
    ) -> List[Product]:
        """Получение отфильтрованных и отсортированных товаров"""
        try:
            async with self.async_session() as session:
                stmt = select(Product)
                
                # Фильтры
                if category_id:
                    stmt = stmt.where(Product.category_id == category_id)
                if min_price is not None:
                    stmt = stmt.where(Product.price >= min_price)
                if max_price is not None:
                    stmt = stmt.where(Product.price <= max_price)
                
                # Сортировка
                if sort_by == 'price':
                    order_by = Product.price.asc() if sort_order == 'asc' else Product.price.desc()
                elif sort_by == 'rating':
                    # Здесь можно добавить сортировку по рейтингу
                    pass
                else:  # по умолчанию по имени
                    order_by = Product.name.asc() if sort_order == 'asc' else Product.name.desc()
                
                stmt = stmt.order_by(order_by)
                result = await session.execute(stmt)
                return result.scalars().all()
        except Exception as e:
            logging.error(f"Ошибка при получении отфильтрованных товаров: {e}")
            return []

    async def toggle_favorite(self, user_id: int, product_id: int) -> bool:
        """Добавление/удаление товара из избранного"""
        try:
            async with self.async_session() as session:
                stmt = select(Favorite).where(
                    Favorite.user_id == user_id,
                    Favorite.product_id == product_id
                )
                result = await session.execute(stmt)
                favorite = result.scalar_one_or_none()
                
                if favorite:
                    await session.delete(favorite)
                else:
                    favorite = Favorite(user_id=user_id, product_id=product_id)
                    session.add(favorite)
                
                await session.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка при работе с избранным: {e}")
            return False

    async def add_review(self, user_id: int, product_id: int, rating: int, text: str) -> bool:
        """Добавление отзыва о товаре"""
        try:
            async with self.async_session() as session:
                review = Review(
                    user_id=user_id,
                    product_id=product_id,
                    rating=rating,
                    text=text
                )
                session.add(review)
                await session.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка при добавлении отзыва: {e}")
            return False

    async def get_user_favorites(self, user_id: int) -> List[Favorite]:
        """Получение избранных товаров пользователя"""
        try:
            async with self.async_session() as session:
                stmt = select(Favorite).options(
                    joinedload(Favorite.product)
                ).where(Favorite.user_id == user_id)
                result = await session.execute(stmt)
                return result.unique().scalars().all()
        except Exception as e:
            logging.error(f"Ошибка при получении избранного: {e}")
            return []

    async def is_favorite(self, user_id: int, product_id: int) -> bool:
        """Проверка, находится ли товар в избранном"""
        try:
            async with self.async_session() as session:
                stmt = select(Favorite).where(
                    Favorite.user_id == user_id,
                    Favorite.product_id == product_id
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logging.error(f"Ошибка при проверке избранного: {e}")
            return False