from .models import async_session
from .models import User, UserProfile, Category, Product, Cart
from sqlalchemy import select, insert, update, delete
import functools

def connection(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return wrapper

@connection
async def get_categories(session):
    return await session.scalars(select(Category))

@connection
async def get_products_by_category(session, category_id: int):
    return await session.scalars(select(Product).where(Product.category_id == category_id))

@connection
async def get_product_by_id(session, product_id: int):
    return await session.scalar(select(Product).where(Product.product_id == product_id))
