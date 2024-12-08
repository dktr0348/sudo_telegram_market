import sqlite3
import logging
import os

class Database:
    def __init__(self, db_file):
        # Убедимся, что путь существует
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        try:
            self.connection = sqlite3.connect(db_file)
            self.cursor = self.connection.cursor()
            self.create_tables()
        except sqlite3.Error as e:
            logging.error(f"Ошибка при подключении к БД: {e}")
            raise
    
    def create_tables(self):
        """Создание необходимых таблиц при первом запуске"""
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица контактов пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT,
                address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица локаций пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                latitude REAL,
                longitude REAL,
                address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица товаров
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT
            )
        ''')
        
        # Таблица корзины
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')
        
        # Таблица регистрации
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS registered_users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                phone_number TEXT,
                location_lat REAL,
                location_lon REAL,
                age INTEGER,
                photo_id TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.connection.commit()
    
    def add_user(self, user_id: int, username: str, first_name: str) -> bool:
        """Добавление нового пользователя"""
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False
    
    def save_contact(self, user_id: int, phone_number: str, address: str = None) -> bool:
        """Сохранение контактных данных пользователя"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO contacts (user_id, phone_number, address)
                VALUES (?, ?, ?)
            ''', (user_id, phone_number, address))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False
    
    def save_location(self, user_id: int, latitude: float, longitude: float, address: str = None) -> bool:
        """Сохранение локации пользователя"""
        try:
            self.cursor.execute('''
                INSERT INTO locations (user_id, latitude, longitude, address)
                VALUES (?, ?, ?, ?)
            ''', (user_id, latitude, longitude, address))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False
    
    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> bool:
        """Добавление товара в корзину"""
        try:
            self.cursor.execute('''
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            ''', (user_id, product_id, quantity))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False
    
    def get_cart(self, user_id: int):
        """Получение содержимого корзины пользователя"""
        self.cursor.execute('''
            SELECT p.name, p.price, c.quantity
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def clear_cart(self, user_id: int) -> bool:
        """Очистка корзины пользователя"""
        try:
            self.cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False
    
    def get_user(self, user_id: int):
        """Получение информации о пользователе"""
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def register_user(self, user_id: int, name: str, phone: str, 
                     location_lat: float, location_lon: float, 
                     age: int, photo_id: str) -> bool:
        """Регистрация пользователя с полными данными"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO registered_users 
                (user_id, name, phone_number, location_lat, location_lon, age, photo_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, phone, location_lat, location_lon, age, photo_id))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка при регистрации пользователя {user_id}: {e}")
            return False
    
    def is_user_registered(self, user_id: int) -> bool:
        """Проверка регистрации пользователя"""
        self.cursor.execute('SELECT user_id FROM registered_users WHERE user_id = ?', (user_id,))
        return bool(self.cursor.fetchone())
    
    def close(self):
        """Закрытие соединения с базой данных"""
        self.connection.close()
    
    def get_user_profile(self, user_id: int):
        """Получение полного профиля пользователя"""
        self.cursor.execute('''
            SELECT ru.*, u.username 
            FROM registered_users ru
            JOIN users u ON ru.user_id = u.user_id
            WHERE ru.user_id = ?
        ''', (user_id,))
        return self.cursor.fetchone() 