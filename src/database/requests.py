from .models import async_session
from .models import User, UserProfile, Category, Product, Cart
from sqlalchemy import select, insert, update, delete
import functools
import logging

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
            return False
            
        # Обновляем только переданные поля
        for field, value in kwargs.items():
            if hasattr(product, field):
                if field == 'price':
                    value = float(value)
                # Если удаляем фото (value=None для photo_id)
                if field == 'photo_id' and value is None:
                    setattr(product, field, None)
                else:
                    setattr(product, field, value)
        
        await session.commit()
        return True
    except Exception as e:
        logging.error(f"Ошибка при редактировании товара: {e}")
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