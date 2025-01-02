from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import src.keyboards as kb
from ..database import requests as db
from ..database.database import Database
import logging
import math
from src.config import STARS_CHANNEL_ID, Config
from ..database.models import OrderStatus, PaymentMethod

router = Router()

# Текущий курс: 1 Star = примерно 0.9-1 рубль
STARS_RATE = 1.9  # Базовый курс конвертации
TINKOFF_CARD = "2200701300001085"
TINKOFF_PHONE = "+79810010348"

class PaymentStates(StatesGroup):
    waiting_for_payment = State()
    confirming_payment = State()

@router.callback_query(F.data == "payment_method")
async def choose_payment_method(callback: CallbackQuery):
    """Выбор способа оплаты"""
    keyboard = kb.InlineKeyboardMarkup(inline_keyboard=[
        [
            kb.InlineKeyboardButton(text="💳 Перевод на карту", callback_data="payment_card"),
            kb.InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="payment_stars")
        ],
        [kb.InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
    ])
    
    await callback.message.edit_text(
        "Выберите способ оплаты:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "payment_card")
async def process_tinkoff_payment(callback: CallbackQuery, db: Database, state: FSMContext):
    """Обработка оплаты через Тинькофф"""
    try:
        cart_items = await db.get_cart(callback.from_user.id)
        if not cart_items:
            await callback.answer("Корзина пуста")
            return
    
        total_amount = sum(item.price * item.quantity for item in cart_items)
        
        # Сохраняем сумму в состоянии
        await state.update_data(amount=total_amount)
        
        # Отправляем инструкции для оплаты
        payment_text = (
            f"💳 Оплата через Тинькофф\n\n"
            f"Сумма к оплате: {total_amount}₽\n\n"
            f"Для оплаты переведите указанную сумму:\n"
            f"💳 На карту: {TINKOFF_CARD}\n"
            f"📱 Или по номеру телефона: {TINKOFF_PHONE}\n\n"
            f"❗️ Важно: В комментарии к переводу укажите код: {callback.from_user.id}\n\n"
            f"После оплаты нажмите кнопку 'Подтвердить оплату'"
        )
        
        await callback.message.edit_text(
            payment_text,
            reply_markup=kb.InlineKeyboardMarkup(inline_keyboard=[
                [kb.InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data="confirm_payment")],
                [kb.InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
            ])
        )
        
        await state.set_state(PaymentStates.waiting_for_payment)
        
    except Exception as e:
        logging.error(f"Ошибка при создании платежа: {e}")
        await callback.answer("Произошла ошибка при создании платежа")

async def get_current_stars_rate(db: Database) -> float:
    """Получение актуального курса из базы данных"""
    try:
        rate = await db.get_stars_rate()
        return rate if rate else 1,9  # Возвращаем дефолтное значение если нет в БД
    except Exception:
        return 1.9  # Дефолтное значение при ошибке

@router.callback_query(F.data == "payment_stars")
async def process_stars_payment(callback: CallbackQuery, state: FSMContext):
    """Обработка оплаты через Stars"""
    try:
        cart_items = await db.get_cart(callback.from_user.id)
        if not cart_items:
            await callback.answer("Корзина пуста")
            return

        # Считаем общую сумму
        total_amount = sum(product.price * quantity for product, quantity in cart_items)
        
        # Конвертируем в Stars
        stars_amount = math.ceil(total_amount / STARS_RATE)

        # Формируем описание товаров
        items_description = "\n".join(
            f"📦 {product.name} x {quantity} шт." 
            for product, quantity in cart_items
        )
        
        # Создаем инвойс для оплаты Stars
        await callback.message.answer_invoice(
            title="Оплата заказа Stars",
            description=f"Товары в заказе:\n{items_description}",
            payload="stars_payment",
            currency="XTR",  # Валюта для Stars
            prices=[
                LabeledPrice(
                    label="Оплата Stars",
                    amount=stars_amount
                )
            ],
            start_parameter="stars_payment",
            protect_content=True
        )

        # Сохраняем детали заказа
        await state.update_data(
            order_details={
                'total_amount': total_amount,
                'stars_amount': stars_amount,
                'payment_method': 'telegram_stars'
            }
        )

    except Exception as e:
        logging.error(f"Ошибка при создании платежа Stars: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при создании платежа",
            reply_markup=kb.main_inline
        )

@router.callback_query(F.data == "confirm_payment", PaymentStates.waiting_for_payment)
async def confirm_p2p_payment(callback: CallbackQuery, state: FSMContext, db: Database):
    """Подтверждение P2P оплаты"""
    try:
        data = await state.get_data()
        amount = data.get('amount')
        
        order_id = await db.create_order(
            user_id=callback.from_user.id,
            total_amount=amount,
            payment_method="tinkoff_p2p",
            status="pending"
        )
        
        if order_id:
            await callback.message.edit_text(
                "✅ Спасибо за оплату!\n"
                "Ваш заказ принят в обработку.\n"
                f"Номер заказа: {order_id}",
                reply_markup=kb.InlineKeyboardMarkup(inline_keyboard=[
                    [kb.InlineKeyboardButton(text="📋 Мои заказы", callback_data="show_orders")]
                ])
            )
            
            await db.clear_cart(callback.from_user.id)
            
        else:
            await callback.message.edit_text(
                "❌ Ошибка при создании заказа",
                reply_markup=kb.main_inline
            )
            
    except Exception as e:
        logging.error(f"Ошибка при подтверждении платежа: {e}")
        await callback.answer("Произошла ошибка при подтверждении платежа")
    finally:
        await state.clear()

@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение возможности оплаты"""
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    """Обработка успешного платежа Stars"""
    try:
        # Возвращаем Stars пользователю
        await message.bot.refund_star_payment(
            message.from_user.id, 
            message.successful_payment.telegram_payment_charge_id
        )
        
        data = await state.get_data()
        order_details = data.get('order_details', {})
        
        # Создаем заказ
        order_id = await db.create_order(
            user_id=message.from_user.id,
            total_amount=order_details['total_amount'],
            payment_method=PaymentMethod.STARS.value,
            status="completed"
        )

        # Получаем товары из корзины
        cart_items = await db.get_cart(message.from_user.id)
        
        # Обновляем количество товаров и создаем записи order_items
        for product, quantity in cart_items:
            # Обновляем количество товара
            await db.update_product_quantity(
                product_id=product.product_id,
                quantity=product.quantity - quantity
            )
            
            # Добавляем запись в order_items
            await db.add_order_item(
                order_id=order_id,
                product_id=product.product_id,
                quantity=quantity,
                price=product.price
            )

        # Записываем транзакцию Stars
        await db.add_stars_transaction(
            order_id=order_id,
            user_id=message.from_user.id,
            stars_amount=order_details['stars_amount'],
            amount_rub=order_details['total_amount'],
            status='completed'
        )

        # Возвращаем Stars пользователю
        stars_to_return = int(order_details['total_amount'])
        
        try:
            await message.bot.send_message(
                message.from_user.id,
                f"⭐ Вам начислено {stars_to_return} Stars за покупку!"
            )
            
            await db.add_stars_transaction(
                order_id=order_id,
                user_id=message.from_user.id,
                stars_amount=stars_to_return,
                amount_rub=order_details['total_amount'],
                status='returned'
            )
        except Exception as stars_error:
            logging.error(f"Ошибка при возврате Stars: {stars_error}")

        # Очищаем корзину
        await db.clear_cart(message.from_user.id)

        # Отправляем подтверждение пользователю с reply клавиатурой
        await message.answer(
            f"✅ Оплата Stars прошла успешно!\n\n"
            f"🆔 Заказ #{order_id}\n"
            f"⭐ Списано Stars: {order_details['stars_amount']}\n"
            f"⭐ Начислено Stars: {stars_to_return}\n"
            f"💰 Сумма: {order_details['total_amount']}₽\n\n"
            f"ID транзакции: {message.successful_payment.telegram_payment_charge_id}",
            reply_markup=kb.main  # Используем основную reply клавиатуру
        )

        # Пробуем отправить уведомление в канал Stars
        try:
            if hasattr(Config, 'STARS_CHANNEL_ID') and Config.STARS_CHANNEL_ID:
                await message.bot.send_message(
                    Config.STARS_CHANNEL_ID,
                    f"💫 Новая транзакция Stars\n\n"
                    f"👤 User ID: {message.from_user.id}\n"
                    f"🆔 Заказ #{order_id}\n"
                    f"⭐ Stars: {order_details['stars_amount']}\n"
                    f"💰 Сумма: {order_details['total_amount']}₽\n"
                    f"🔖 ID транзакции: {message.successful_payment.telegram_payment_charge_id}"
                )
        except Exception as channel_error:
            logging.warning(f"Не удалось отправить уведомление в канал Stars: {channel_error}")

        await state.clear()

    except Exception as e:
        logging.error(f"Ошибка при обработке платежа Stars: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке платежа",
            reply_markup=kb.main  # В случае ошибки тоже используем reply клавиатуру
        )

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Отмена платежа"""
    await state.clear() 
    await callback.message.edit_text(
        "❌ Оплата отменена",
        reply_markup=kb.main_inline
    ) 

# Функция для безопасной конвертации с округлением вверх
def convert_to_stars(amount_rub: float) -> int:
    stars = amount_rub / STARS_RATE
    return math.ceil(stars)  # Округляем вверх до целого числа Stars 

@router.message(Command("stars"))
async def check_stars_balance(message: Message, bot):
    """Проверка баланса Stars"""
    try:
        # Получаем информацию о канале
        channel_info = await bot.get_chat(STARS_CHANNEL_ID)
        
        # Получаем баланс Stars (если доступно через API)
        # Примечание: не все методы могут быть доступны
        balance_text = (
            f"⭐ Баланс Stars канала {channel_info.title}:\n"
            f"💰 Доступно для вывода: {channel_info.stars_balance}\n"
            f"📊 Курс конвертации: 1 Star = {STARS_RATE}₽"
        )
        
        await message.answer(balance_text)
    except Exception as e:
        logging.error(f"Ошибка при проверке баланса Stars: {e}")
        await message.answer("❌ Не удалось получить информацию о балансе Stars") 