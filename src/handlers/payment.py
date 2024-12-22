from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from ..state import Payment
from ..keyboards import main
import logging

router = Router()

PAYMENT_METHODS = {
    'card': 'Банковская карта',
    'spb': 'spb',
    'other': 'other',
    'crypto': 'Криптовалюта'
}

async def get_payment_keyboard(order_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Банковская карта", callback_data=f"pay_card_{order_id}")],
        [InlineKeyboardButton(text="📱 СПб", callback_data=f"pay_spb_{order_id}")],
        [InlineKeyboardButton(text="💰 other", callback_data=f"pay_other_{order_id}")],
        [InlineKeyboardButton(text="₿ Криптовалюта", callback_data=f"pay_crypto_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
    ])
    return keyboard

@router.message(F.text == "Оформить заказ")
async def process_checkout(message: Message, state: FSMContext, db):
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("Ваша корзина пуста!")
        return
    
    # Проверяем наличие товаров
    for name, price, quantity, product_id in cart_items:
        product = await db.get_product_by_id(product_id)
        if not product or product.quantity < quantity:
            await message.answer(f"Товар '{name}' недоступен в запрошенном количестве")
            return
    
    # Создаем заказ
    total = sum(price * quantity for _, price, quantity, _ in cart_items)
    order_id = await db.create_order(user_id, cart_items, total)
    
    if not order_id:
        await message.answer("Ошибка при создании заказа")
        return
    
    await state.set_state(Payment.method)
    await state.update_data(order_id=order_id)
    
    text = (
        f"💰 Сумма к оплате: {total}₽\n\n"
        "Выберите способ оплаты:"
    )
    
    keyboard = await get_payment_keyboard(order_id)
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith('pay_'))
async def process_payment(callback: CallbackQuery, state: FSMContext, db):
    try:
        _, method, order_id = callback.data.split('_')
        order = await db.get_order(int(order_id))
        
        if not order:
            await callback.message.answer("Заказ не найден")
            return
        
        # Здесь будет интеграция с платежной системой
        payment_info = {
            'card': "Отправьте данные карты в формате: НОМЕР КАРТЫ ММ/ГГ CVC",
            'spb': "Отправьте номер ",
            'other': "Отправьте номер other кошелька",
            'crypto': "Выберите криптовалюту для оплаты"
        }
        
        await state.set_state(Payment.processing)
        await state.update_data(payment_method=method, order_id=order_id)
        await callback.message.edit_text(
            f"Способ оплаты: {PAYMENT_METHODS[method]}\n"
            f"Сумма: {order.total}₽\n\n"
            f"{payment_info[method]}"
        )
        
    except Exception as e:
        logging.error(f"Ошибка при обработке платежа: {e}")
        await callback.message.answer("Произошла ошибка при обработке платежа")

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Оплата отменена")
    await callback.message.answer("Выберите действие:", reply_markup=main)

@router.message(Payment.processing)
async def process_payment_details(message: Message, state: FSMContext, db):
    data = await state.get_data()
    method = data.get('payment_method')
    order_id = data.get('order_id')
    
    # Здесь будет обработка платежных данных
    # В реальном приложении здесь должна быть интеграция с платежным шлюзом
    
    try:
        # Имитация обработки платежа
        order = await db.get_order(order_id)
        if not order:
            await message.answer("Заказ не найден")
            return
            
        # Обновляем количество товаров
        cart_items = await db.get_cart(message.from_user.id)
        for name, _, quantity in cart_items:
            await db.update_product_quantity(name, quantity)
        
        # Очищаем корзину
        await db.clear_cart(message.from_user.id)
        
        # Обновляем статус заказа
        await db.update_order_status(order_id, 'paid')
        
        await message.answer(
            "✅ Заказ успешно оплачен!\n"
            f"Номер заказа: {order_id}\n"
            f"Способ оплаты: {PAYMENT_METHODS[method]}\n"
            f"Сумма: {order.total}₽",
            reply_markup=main
        )
        
    except Exception as e:
        logging.error(f"Ошибка при обработке платежных данных: {e}")
        await message.answer("Произошла ошибка при обработке платежа", reply_markup=main)
    
    finally:
        await state.clear() 