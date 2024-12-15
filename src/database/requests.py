from .models import async_session
from .models import User, UserProfile, Category, Product, Cart
from sqlalchemy import select, insert, update, delete

async def get_categories():
    async with async_session() as session:
        return await session.scalars(select(Category))

async def get_products_by_category(category_id: int):
    async with async_session() as session:
        return await session.scalars(select(Product).where(Product.category_id == category_id))

async def get_product_by_id(product_id: int):
    async with async_session() as session:
        return await session.scalar(select(Product).where(Product.product_id == product_id))
