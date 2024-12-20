from aiogram import F
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart, BaseFilter
from src.config import admin_ids, super_admin_id
import src.state as st
import src.keyboards as kb
import src.database.requests as db
from aiogram.fsm.context import FSMContext
import logging

router = Router()

class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        is_admin = user_id in admin_ids
        logging.info(f"Проверка прав администратора для пользователя {user_id}: {is_admin}")
        return is_admin

# Создаем экземпляр фильтра
admin_filter = AdminFilter()

@router.message(Command('admin'))
async def cmd_admin(message: Message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        await message.answer(
            "Добро пожаловать в панель администратора!",
            reply_markup=kb.admin_main
        )
    else:
        await message.answer("У вас нет прав администратора.")

@router.message(admin_filter, F.text == 'Выйти')
async def exit_admin(message: Message):
    await message.answer(
        "Вы вышли из режима администратора",
        reply_markup=kb.main
    )

@router.message(admin_filter, F.text == 'Добавить категорию')
async def add_category(message: Message, state: FSMContext):
    await state.set_state(st.AddCategory.name)
    await message.answer("Введите название категории:")

@router.message(admin_filter, st.AddCategory.name)
async def add_category_sure(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(st.AddCategory.confirm)
    await message.answer(
        f"Вы уверены, что хотите добавить категорию? - {message.text}",
        reply_markup=kb.confirm
    )

@router.callback_query(admin_filter, F.data == 'ok-sure', st.AddCategory.confirm)
async def add_category_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await db.add_category(data['name'])
    await callback.message.answer(
        "Категория добавлена",
        reply_markup=kb.admin_main
    )
    await state.clear()

@router.callback_query(admin_filter, F.data == 'cancel-sure', st.AddCategory.confirm)
async def add_category_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Добавление категории отменено",
        reply_markup=kb.admin_main
    )
    await state.clear()

@router.message(admin_filter, F.text == 'Удалить категорию')
async def delete_category_select(message: Message, state: FSMContext):
    await state.set_state(st.DeleteCategory.select)
    keyboard = await kb.delete_categories()
    await message.answer(
        "Выберите категорию для удаления:",
        reply_markup=keyboard
    )

@router.callback_query(admin_filter, F.data.startswith("delete_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.set_state(st.DeleteCategory.confirm)
    await state.update_data(category_id=category_id)
    await callback.message.answer(
        "Вы уверены, что хотите удалить эту категорию?",
        reply_markup=kb.confirm
    )

@router.callback_query(admin_filter, F.data == 'ok-sure', st.DeleteCategory.confirm)
async def delete_category_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await db.delete_category(data['category_id'])
    await callback.message.answer(
        "Категория удалена",
        reply_markup=kb.admin_main
    )
    await state.clear()

@router.message(admin_filter, F.text == 'Добавить товар')
async def add_product(message: Message, state: FSMContext):
    await state.set_state(st.AddProduct.category)
    keyboard = await kb.admin_categories()
    await message.answer(
        "Выберите категорию для добавления товара:",
        reply_markup=keyboard
    )

@router.callback_query(admin_filter, F.data.startswith("addcategory_"))
async def add_product_name(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)
    await state.set_state(st.AddProduct.name)
    await callback.message.answer("Введите название товара:")
    await callback.answer()

@router.message(admin_filter, st.AddProduct.name)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(st.AddProduct.description)
    await message.answer("Введите описание товара:")

@router.message(admin_filter, st.AddProduct.description)
async def add_product_price(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(st.AddProduct.price)
    await message.answer("Введите цену товара:")

@router.message(admin_filter, st.AddProduct.price)
async def add_product_confirm(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(st.AddProduct.confirm)
        data = await state.get_data()
        await message.answer(
            f"Вы уверены, что хотите добавить этот товар?\n\n"
            f"Название: {data['name']}\n"
            f"Описание: {data['description']}\n"
            f"Цена: {data['price']}₽",
            reply_markup=kb.confirm
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену (число)")

@router.callback_query(admin_filter, F.data == 'ok-sure', st.AddProduct.confirm)
async def add_product_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product = await db.add_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        category_id=data['category_id']
    )
    if product:
        await callback.message.answer(
            "Товар успешно добавлен",
            reply_markup=kb.admin_main
        )
    else:
        await callback.message.answer(
            "Ошибка при добавлении товара",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.callback_query(admin_filter, F.data == 'cancel-sure', st.AddProduct.confirm)
async def add_product_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Добавление товара отменено",
        reply_markup=kb.admin_main
    )
    await state.clear()

@router.message(admin_filter, F.text == 'Удалить товар')
async def delete_product_select(message: Message, state: FSMContext):
    await state.set_state(st.DeleteProduct.select)
    keyboard = await kb.delete_product()
    await message.answer(
        "Выберите товар для удаления:",
        reply_markup=keyboard
    )

@router.callback_query(admin_filter, F.data.startswith('proddelete_'))
async def process_product_deletion(callback: CallbackQuery, state: FSMContext):
    try:
        product_id = int(callback.data.replace('proddelete_', ''))
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.message.answer("Товар не найден", reply_markup=kb.admin_main)
            return
            
        await state.set_state(st.DeleteProduct.confirm)
        await state.update_data(product_id=product_id)
        await callback.message.answer(
            f"Вы уверены, что хотите удалить товар '{product.name}'?",
            reply_markup=kb.confirm
        )
    except Exception as e:
        logging.error(f"Ошибка при выборе товара: {e}")
        await callback.message.answer("Ошибка при выборе товара", reply_markup=kb.admin_main)
        await state.clear()

@router.callback_query(admin_filter, F.data == 'ok-sure', st.DeleteProduct.confirm)
async def delete_product_callback(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        if await db.delete_product(data['product_id']):
            await callback.message.answer("Товар удален", reply_markup=kb.admin_main)
        else:
            await callback.message.answer("Ошибка при удалении", reply_markup=kb.admin_main)
    except Exception as e:
        logging.error(f"Ошибка при удалении товара: {e}")
        await callback.message.answer("Ошибка при удалении", reply_markup=kb.admin_main)
    finally:
        await state.clear()

@router.callback_query(F.data.in_({'cancel-sure', 'cancel_delete'}))
async def cancel_delete_action(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Действие отменено", reply_markup=kb.admin_main)
    await state.clear()