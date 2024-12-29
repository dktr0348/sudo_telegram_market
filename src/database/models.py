import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, CheckConstraint, Enum
from sqlalchemy.orm import relationship, validates, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем асинхронный движок
engine = create_async_engine(
    "sqlite+aiosqlite:///bot_database.db",
    echo=True
)

# Создаем фабрику асинхронных сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    reg_date = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    
    profile = relationship('UserProfile', back_populates='user', uselist=False)
    cart_items = relationship('Cart', back_populates='user', cascade='all, delete-orphan')
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan')
    favorites = relationship('Favorite', back_populates='user', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='user', cascade='all, delete-orphan')

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    name = Column(String)
    phone_number = Column(String)
    email = Column(String)
    location_lat = Column(Float)
    location_lon = Column(Float)
    age = Column(Integer)
    photo_id = Column(String)
    
    user = relationship('User', back_populates='profile')

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    
    products = relationship('Product', back_populates='category', cascade='all, delete-orphan')

class Product(Base):
    __tablename__ = 'products'
    
    product_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'))
    name = Column(String)
    description = Column(Text)
    price = Column(Float)
    photo_id = Column(String)
    quantity = Column(Integer, default=0)
    
    category = relationship('Category', back_populates='products')
    cart_items = relationship('Cart', back_populates='product', cascade='all, delete-orphan')
    favorites = relationship('Favorite', back_populates='product', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='product', cascade='all, delete-orphan')
    
    # Проверка, что количество товара не может быть отрицательным
    __table_args__ = (
        CheckConstraint(quantity >= 0, name='check_quantity_positive'),
    )
    
    @validates('quantity')
    def validate_quantity(self, key, value):
        """Валидация количества товара"""
        if value < 0:
            raise ValueError("Количество товара не может быть отрицательным")
        return value

    @property
    def average_rating(self):
        """Вычисление среднего рейтинга товара"""
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)

class Cart(Base):
    __tablename__ = 'cart'
    
    cart_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    
    user = relationship('User', back_populates='cart_items')
    product = relationship('Product', back_populates='cart_items')
    
    # Проверка, что количество в корзине положительное
    __table_args__ = (
        CheckConstraint(quantity > 0, name='check_cart_quantity_positive'),
    )
    
    @validates('quantity')
    def validate_quantity(self, key, value):
        """Валидация количества товара в корзине"""
        if value <= 0:
            raise ValueError("Количество товара в корзине должно быть положительным")
        return value
    
    def check_available_quantity(self):
        """Проверка доступного количества товара"""
        if self.quantity > self.product.quantity:
            raise ValueError(
                f"Недостаточно товара на складе. Доступно: {self.product.quantity}, "
                f"запрошено: {self.quantity}"
            )

class OrderStatus(enum.Enum):
    NEW = "new"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethod(enum.Enum):
    CASH = "cash"
    CARD = "card"
    ONLINE = "online"

class DeliveryMethod(enum.Enum):
    COURIER = "courier"
    PICKUP = "pickup"

class Order(Base):
    __tablename__ = 'orders'

    order_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    total_amount = Column(Float, nullable=False)
    delivery_address = Column(String)
    payment_method = Column(Enum(PaymentMethod))
    delivery_method = Column(Enum(DeliveryMethod))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = 'order_items'

    item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'))
    product_id = Column(Integer, ForeignKey('products.product_id'))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class Favorite(Base):
    __tablename__ = 'favorites'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'))
    added_at = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='favorites')
    product = relationship('Product', back_populates='favorites')

class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'))
    rating = Column(Integer, nullable=False)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='reviews')
    product = relationship('Product', back_populates='reviews')
    
    # Ограничения на рейтинг (от 1 до 5)
    __table_args__ = (
        CheckConstraint(rating >= 1, name='check_rating_min'),
        CheckConstraint(rating <= 5, name='check_rating_max'),
    )