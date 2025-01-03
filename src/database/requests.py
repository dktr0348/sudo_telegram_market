from .models import async_session, User, UserProfile, Category, Product, Cart
from .models import Order, OrderItem, StarsTransaction, OrderStatus, PaymentMethod, Review
from sqlalchemy import select, insert, update, delete, or_
import functools
import logging
from typing import List, Optional
from datetime import datetime

def connection(func):
    """Декоратор для автоматического управления сессией базы данных"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return wrapper

@connection
async def get_categories(session):
    result = await session.scalars(select(Category))
    return [cat for cat in result]

@connection
async def get_products_by_category(session, category_id: int):
    result = await session.scalars(select(Product).where(Product.category_id == category_id))
    return [prod for prod in result]

@connection
async def get_product_by_id(session, product_id: int):
    return await session.scalar(select(Product).where(Product.product_id == product_id))

@connection
async def add_category(session, name: str):
    category = Category(name=name)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category

@connection
async def delete_category(session, category_id: int):
    category = await session.get(Category, category_id)
    if category:
        await session.delete(category)
        await session.commit()
        return True
    return False

@connection
async def add_product(session, name: str, description: str, price: float, category_id: int, photo_id: str = None):
    try:
        price = float(price)
        product = Product(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            photo_id=photo_id
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product
    except ValueError:
        return None

@connection
async def delete_product(session, product_id: int):
    product = await session.get(Product, product_id)
    if product:
        await session.delete(product)
        await session.commit()
        return True
    return False

@connection
async def get_all_products(session):
    result = await session.scalars(select(Product))
    return [prod for prod in result]

@connection
async def get_admins(session):
    try:
        # Получаем всех пользователей с флагом is_admin = True
        result = await session.scalars(select(User).where(User.is_admin == True))
        admins = [admin for admin in result]
        logging.info(f"Получено {len(admins)} администраторов")
        return admins
    except Exception as e:
        logging.error(f"Ошибка при получении списка администраторов: {e}")
        return []

@connection
async def delete_admin(session, admin_id: int):
    try:
        # Получаем пользователя
        admin = await session.get(User, admin_id)
        if admin:
            # Снимаем флаг администратора
            admin.is_admin = False
            await session.commit()
            logging.info(f"Администратор {admin_id} успешно удален")
            return True
        logging.warning(f"Администратор {admin_id} не найден")
        return False
    except Exception as e:
        logging.error(f"Ошибка при удалении администратора {admin_id}: {e}")
        return False

@connection
async def add_admin(session, admin_id: int) -> bool:
    """Добавление нового администратора"""
    try:
        # Проверяем существование пользователя
        user = await session.get(User, admin_id)
        if not user:
            # Если пользователь не существует, создаем его
            user = User(user_id=admin_id)
            session.add(user)
        
        # Устанавливаем флаг is_admin
        user.is_admin = True
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при добавлении администратора: {e}")
        return False

@connection
async def edit_product(session, product_id: int, **kwargs) -> bool:
    """Редактирование товара
    
    Args:
        product_id (int): ID товара
        **kwargs: Поля для обновления (name, description, price, category_id, photo_id)
    """
    try:
        product = await session.get(Product, product_id)
        if not product:
            logging.error(f"Товар с ID {product_id} не найден")
            return False
            
        # Обновляем только переданные поля
        for field, value in kwargs.items():
            if hasattr(product, field):
                if field == 'price' and value is not None:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        logging.error(f"Некорректное значение цены: {value}")
                        continue
                
                # Обработка фото
                if field == 'photo_id':
                    logging.info(f"Обновление фото у товара {product_id}: {value}")
                
                setattr(product, field, value)
                logging.info(f"Обновлено поле {field} у товара {product_id}: {value}")
        
        await session.commit()
        logging.info(f"Товар {product_id} успешно обновлен")
        return True
    except Exception as e:
        logging.error(f"Ошибка при редактировании товара {product_id}: {e}")
        await session.rollback()
        return False

@connection
async def is_admin(session, user_id: int) -> bool:
    """Проверка является ли пользователь администратором"""
    try:
        user = await session.get(User, user_id)
        return user is not None and user.is_admin
    except Exception as e:
        logging.error(f"Ошибка при проверке прав администратора {user_id}: {e}")
        return False

@connection
async def get_cart_item_quantity(session, user_id: int, product_id: int) -> int:
    """Получение количества товара в корзине пользователя"""
    result = await session.execute(
        select(Cart.quantity)
        .where(Cart.user_id == user_id)
        .where(Cart.product_id == product_id)
    )
    quantity = result.scalar()
    return quantity or 0

@connection
async def add_to_cart(session, user_id: int, product_id: int, quantity: int) -> bool:
    """Добавление/обновление товара в корзине"""
    try:
        cart_item = await session.scalar(
            select(Cart)
            .where(Cart.user_id == user_id)
            .where(Cart.product_id == product_id)
        )
        
        if cart_item:
            cart_item.quantity = quantity
        else:
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            session.add(cart_item)
            
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при добавлении в корзину: {e}")
        return False

@connection
async def clear_cart(session, user_id: int) -> bool:
    """Очистка корзины пользователя"""
    try:
        await session.execute(
            delete(Cart).where(Cart.user_id == user_id)
        )
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при очистке корзины: {e}")
        return False

@connection
async def get_cart(session, user_id: int) -> list:
    """Получение содержимого корзины пользователя"""
    result = await session.execute(
        select(Product, Cart.quantity)
        .join(Cart, Cart.product_id == Product.product_id)
        .where(Cart.user_id == user_id)
    )
    return result.all()

@connection
async def remove_from_cart(session, user_id: int, product_id: int) -> bool:
    """Удаление товара из корзины"""
    try:
        await session.execute(
            delete(Cart).where(
                Cart.user_id == user_id,
                Cart.product_id == product_id
            )
        )
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при удалении из корзины: {e}")
        return False

@connection
async def get_stars_transactions(session, user_id: int = None, limit: int = 10) -> List[StarsTransaction]:
    """Получение истории транзакций Stars"""
    try:
        if user_id:
            stmt = select(StarsTransaction).where(
                StarsTransaction.user_id == user_id
            ).order_by(
                StarsTransaction.created_at.desc()
            ).limit(limit)
        else:
            stmt = select(StarsTransaction).order_by(
                StarsTransaction.created_at.desc()
            ).limit(limit)
            
        result = await session.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        logging.error(f"Ошибка при получении истории Stars: {e}")
        return []

@connection
async def add_stars_transaction(
    session,
    order_id: int,
    user_id: int,
    stars_amount: int,
    amount_rub: float,
    status: str = "completed"
) -> bool:
    """Добавление новой транзакции Stars"""
    try:
        transaction = StarsTransaction(
            order_id=order_id,
            user_id=user_id,
            stars_amount=stars_amount,
            amount_rub=amount_rub,
            status=status
        )
        session.add(transaction)
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при добавлении транзакции Stars: {e}")
        await session.rollback()
        return False

@connection
async def create_order(session, user_id: int, total_amount: float, payment_method: str, status: str = "pending") -> int:
    """Создание нового заказа"""
    order = Order(
        user_id=user_id,
        total_amount=total_amount,
        payment_method=payment_method,
        status=status
    )
    session.add(order)
    await session.commit()
    return order.order_id

@connection
async def get_user_orders(session, user_id: int):
    """Получение заказов пользователя"""
    try:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        logging.error(f"Ошибка при получении заказов: {e}")
        return []

@connection
async def update_product_quantity(session, product_id: int, quantity: int):
    """Обновление количества товара"""
    await session.execute(
        update(Product)
        .where(Product.product_id == product_id)
        .values(quantity=quantity)
    )
    await session.commit()

@connection
async def add_order_item(session, order_id: int, product_id: int, quantity: int, price: float):
    """Добавление товара в заказ"""
    order_item = OrderItem(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        price=price
    )
    session.add(order_item)
    await session.commit()

@connection
async def get_product_reviews(session, product_id: int):
    """Получение отзывов о товаре"""
    try:
        result = await session.execute(
            select(Review)
            .join(User)  # Присоединяем таблицу пользователей
            .where(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        logging.error(f"Ошибка при получении отзывов: {e}")
        return []

@connection
async def add_review(session, user_id: int, product_id: int, rating: int, text: str) -> bool:
    """Добавление нового отзыва"""
    try:
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
        await session.rollback()
        return False

@connection
async def update_user_language(session, user_id: int, language: str) -> bool:
    """Обновление языка пользователя"""
    try:
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(language=language)
        )
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении языка: {e}")
        return False

@connection
async def update_user_notifications(session, user_id: int, enabled: bool) -> bool:
    """Обновление настроек уведомлений пользователя"""
    try:
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(notifications=enabled)
        )
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении настроек уведомлений: {e}")
        return False

@connection
async def get_user_language(session, user_id: int) -> str:
    """Получение языка пользователя"""
    try:
        result = await session.execute(
            select(User.language)
            .where(User.user_id == user_id)
        )
        language = result.scalar()
        return language or 'ru'  # Возвращаем 'ru' если язык не установлен
    except Exception as e:
        logging.error(f"Ошибка при получении языка пользователя: {e}")
        return 'ru'  # По умолчанию возвращаем русский язык

@connection
async def get_user_notifications(session, user_id: int) -> bool:
    """Получение статуса уведомлений пользователя"""
    try:
        result = await session.execute(
            select(User.notifications)
            .where(User.user_id == user_id)
        )
        return result.scalar() or False
    except Exception as e:
        logging.error(f"Ошибка при получении статуса уведомлений: {e}")
        return False

@connection
async def get_users_with_notifications(session) -> List[User]:
    """Получение пользователей с включенными уведомлениями"""
    try:
        result = await session.execute(
            select(User)
            .where(User.notifications == True)
        )
        return result.scalars().all()
    except Exception as e:
        logging.error(f"Ошибка при получении пользователей с уведомлениями: {e}")
        return []

@connection
async def get_review(session, review_id: int) -> Optional[Review]:
    """Получение отзыва по ID"""
    try:
        result = await session.execute(
            select(Review)
            .where(Review.id == review_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logging.error(f"Ошибка при получении отзыва: {e}")
        return None

@connection
async def update_order_status(session, order_id: int, new_status: str) -> bool:
    """Обновление статуса заказа"""
    try:
        await session.execute(
            update(Order)
            .where(Order.order_id == order_id)
            .values(status=new_status)
        )
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении статуса заказа: {e}")
        await session.rollback()
        return False

@connection
async def update_payment_status(session, order_id: int, status: str) -> bool:
    """Обновление статуса оплаты"""
    try:
        await session.execute(
            update(Order)
            .where(Order.order_id == order_id)
            .values(payment_status=status)
        )
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении статуса оплаты: {e}")
        await session.rollback()
        return False

@connection
async def get_order(session, order_id: int):
    """Получение заказа по ID"""
    try:
        result = await session.execute(
            select(Order).where(Order.order_id == order_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logging.error(f"Ошибка при получении заказа: {e}")
        return None