from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    registration_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Отношения
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    cart_items = relationship("Cart", back_populates="user")

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    name = Column(String)
    phone_number = Column(String)
    email = Column(String)
    location_lat = Column(Float)
    location_lon = Column(Float)
    age = Column(Integer)
    photo_id = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    user = relationship("User", back_populates="profile")

class Product(Base):
    __tablename__ = 'products'
    
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    cart_items = relationship("Cart", back_populates="product")

class Cart(Base):
    __tablename__ = 'cart'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    product_id = Column(Integer, ForeignKey('products.product_id'))
    quantity = Column(Integer, default=1)
    added_date = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items") 