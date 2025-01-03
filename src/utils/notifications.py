from aiogram import Bot
from ..database import requests as db
import logging
from typing import List, Optional

class NotificationManager:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_notification(self, user_id: int, text: str, disable_notification: bool = False) -> bool:
        """Отправка уведомления пользователю"""
        try:
            if await db.get_user_notifications(user_id):
                await self.bot.send_message(
                    user_id, 
                    text, 
                    disable_notification=disable_notification
                )
                return True
            return False
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")
            return False

    async def notify_order_status(self, order_id: int, new_status: str):
        """Уведомление об изменении статуса заказа"""
        try:
            order = await db.get_order(order_id)
            if order:
                text = f"📦 Заказ #{order_id}\n"
                text += f"Статус изменен на: {new_status}"
                await self.send_notification(order.user_id, text)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления о статусе заказа: {e}")

    async def notify_new_product(self, product_id: int):
        """Уведомление о новом товаре"""
        try:
            product = await db.get_product_by_id(product_id)
            if product:
                text = f"🆕 Новый товар в магазине!\n\n"
                text += f"📝 {product.name}\n"
                text += f"💰 Цена: {product.price}₽"
                
                # Получаем всех пользователей с включенными уведомлениями
                users = await db.get_users_with_notifications()
                for user in users:
                    await self.send_notification(user.user_id, text)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления о новом товаре: {e}")

    async def notify_payment_status(self, order_id: int, status: str):
        """Уведомление о статусе оплаты"""
        try:
            order = await db.get_order(order_id)
            if order:
                text = f"💳 Оплата заказа #{order_id}\n"
                text += f"Статус: {status}"
                await self.send_notification(order.user_id, text)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления об оплате: {e}")

    async def notify_review_response(self, review_id: int, response: str):
        """Уведомление об ответе на отзыв"""
        try:
            review = await db.get_review(review_id)
            if review:
                text = f"📝 Получен ответ на ваш отзыв:\n\n"
                text += f"Ваш отзыв: {review.text}\n"
                text += f"Ответ: {response}"
                await self.send_notification(review.user_id, text)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления об ответе на отзыв: {e}")