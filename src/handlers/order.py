from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from ..database.database import Database
import src.keyboards as kb
from ..database.models import OrderStatus, PaymentMethod, DeliveryMethod
import logging

router = Router()

class OrderState(StatesGroup):
    waiting_for_address = State()
    waiting_for_delivery = State()
    waiting_for_payment = State()
    confirming = State()

@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext, db: Database):
    """Начало оформления заказа"""
    try:
        # Проверяем наличие товаров в корзине
        cart_items = await db.get_cart(callback.from_user.id)
        if not cart_items:
            await callback.answer("Корзина пуста!")
            return

        await state.set_state(OrderState.waiting_for_address)
        await callback.message.answer(
            "📍 Пожалуйста, введите адрес достаки:",
            reply_markup=kb.cancel_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при начале оформления заказа: {e}")
        await callback.answer("Произошла ошибка")

@router.message(OrderState.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса доставки"""
    await state.update_data(delivery_address=message.text)
    await state.set_state(OrderState.waiting_for_delivery)
    await message.answer(
        "🚚 Выберите способ доставки:",
        reply_markup=kb.delivery_method_keyboard()
    )

@router.callback_query(OrderState.waiting_for_delivery)
async def process_delivery(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора способа доставки"""
    delivery_method = callback.data.split('_')[1]
    await state.update_data(delivery_method=delivery_method)
    await state.set_state(OrderState.waiting_for_payment)
    await callback.message.edit_text(
        "💳 Выберите способ оплаты:",
        reply_markup=kb.payment_method_keyboard()
    )

@router.callback_query(OrderState.waiting_for_payment)
async def process_payment(callback: CallbackQuery, state: FSMContext, db: Database):
    """Обработка выбора способа оплаты"""
    payment_method = callback.data.split('_')[1]
    data = await state.get_data()
    await state.update_data(payment_method=payment_method)
    
    # Формируем сообщение с деталями заказа
    cart_items = await db.get_cart(callback.from_user.id)
    total = sum(product.price * quantity for product, quantity in cart_items)
    
    order_details = (
        "📋 Детали заказа:\n\n"
        f"📍 Адрес: {data['delivery_address']}\n"
        f"🚚 Доставка: {data['delivery_method']}\n"
        f"💳 Оплата: {payment_method}\n"
        f"💰 Итого: {total}₽\n\n"
        "Подтверждаете заказ?"
    )
    
    await state.set_state(OrderState.confirming)
    await callback.message.edit_text(
        order_details,
        reply_markup=kb.confirm_order_keyboard()
    )

@router.callback_query(OrderState.confirming, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, db: Database):
    """Подтверждение и создание заказа"""
    try:
        data = await state.get_data()
        cart_items = await db.get_cart(callback.from_user.id)
        total = sum(product.price * quantity for product, quantity in cart_items)
        
        order = await db.create_order(
            user_id=callback.from_user.id,
            delivery_address=data['delivery_address'],
            delivery_method=data['delivery_method'],
            payment_method=data['payment_method'],
            total_amount=total,
            items=cart_items
        )
        
        if order:
            await db.clear_cart(callback.from_user.id)
            text = (
                f"✅ Заказ №{order.order_id} успешно создан!\n"
                "Мы свяжемся с вами для подтверждения."
            )
            # Отправляем новое сообщение вместо редактирования
            await callback.message.answer(text, reply_markup=kb.main)
            # Удаляем старое сообщение
            await callback.message.delete()
            await callback.answer("Заказ успешно создан!")
        else:
            await callback.answer("Ошибка при создании заказа")
        
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка при создании заказа: {e}")
        await callback.answer("Произошла ошибка при создании заказа")

@router.message(F.text == "❌ Отменить")
async def cancel_order_reply(message: Message, state: FSMContext):
    """Отмена через reply клавиатуру"""
    await state.clear()
    await message.answer(
        "❌ Оформление заказа отменено",
        reply_markup=kb.main
    )

@router.callback_query(F.data == "cancel_checkout")
async def cancel_checkout(callback: CallbackQuery, state: FSMContext):
    """Отмена через inline кнопку"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Оформление заказа отменено",
        reply_markup=kb.main_inline
    ) 