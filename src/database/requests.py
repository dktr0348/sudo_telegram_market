from .models import async_session
from .models import User, UserProfile, Category, Product, Cart
from sqlalchemy import select, insert, update, delete
import functools

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
async def add_product(session, name: str, description: str, price: float, category_id: int):
    try:
        price = float(price)
        product = Product(
            name=name,
            description=description,
            price=price,
            category_id=category_id
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