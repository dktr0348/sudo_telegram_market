from aiogram import F
from aiogram import Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, CommandStart, BaseFilter
from src.config import admin_ids, super_admin_id
import src.state as st
import src.keyboards as kb
import src.database.requests as db
from aiogram.fsm.context import FSMContext
import logging

router = Router()

class SuperAdminFilter(BaseFilter):
    """Фильтр для проверки прав супер-администратора"""
    async def __call__(self, message: Message | CallbackQuery) -> bool:
        if isinstance(message, Message):
            user_id = message.from_user.id
        else:
            user_id = message.from_user.id
        return user_id == super_admin_id

super_admin_filter = SuperAdminFilter()

@router.message(Command('superadmin'))
async def super_admin_cmd(message: Message):
    """Обработчик команды суперадмина"""
    if message.from_user.id == super_admin_id:
        await message.answer("👑 Вы супер-администратор", reply_markup=kb.admin_main)
    else:
        await message.answer("❌ У вас нет прав супер-администратора")

@router.message(F.text == '👥 Добавить админа')
async def add_admin_cmd(message: Message, state: FSMContext):
    """Начало процесса добавления администратора"""
    if message.from_user.id != super_admin_id:
        await message.answer("❌ У вас нет прав для добавления администраторов")
        return
        
    await state.set_state(st.AddAdmin.name)
    await message.answer(
        "👤 Введите ID пользователя для добавления в администраторы:",
        reply_markup=kb.cancel_kb
    )

@router.message(F.text == "❌ Отменить редактирование", st.AddAdmin.name)
async def cancel_add_admin(message: Message, state: FSMContext):
    """Отмена добавления администратора"""
    await state.clear()
    await message.answer(
        "❌ Добавление администратора отменено",
        reply_markup=kb.admin_main
    )

@router.message(st.AddAdmin.name)
async def add_admin_confirm(message: Message, state: FSMContext):
    """Подтверждение добавления администратора"""
    if message.from_user.id != super_admin_id:
        await message.answer("❌ У вас нет прав для добавления администраторов")
        await state.clear()
        return
        
    try:
        admin_id = int(message.text)
        await state.update_data(admin_id=admin_id)
        await state.set_state(st.AddAdmin.confirm)
        await message.answer(
            f"❓ Вы уверены, что хотите добавить пользователя {admin_id} в администраторы?",
            reply_markup=kb.confirm
        )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректный ID пользователя (целое число)",
            reply_markup=kb.admin_main
        )

@router.callback_query(F.data == 'ok-sure', st.AddAdmin.confirm)
async def add_admin_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка подтверждения добавления администратора"""
    if callback.from_user.id != super_admin_id:
        await callback.message.answer("❌ У вас нет прав для добавления администраторов")
        await state.clear()
        return
        
    data = await state.get_data()
    admin_id = data['admin_id']
    
    if await db.add_admin(admin_id):
        await callback.message.answer(
            f"✅ Пользователь {admin_id} добавлен в администраторы",
            reply_markup=kb.admin_main
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при добавлении администратора",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.message(F.text == '🚫 Удалить админа')
async def delete_admin_cmd(message: Message, state: FSMContext):
    """Начало процесса удаления администратора"""
    if message.from_user.id != super_admin_id:
        await message.answer("❌ У вас нет прав для удаления администраторов")
        return
        
    await state.set_state(st.DeleteAdmin.select)
    keyboard = await kb.delete_admins()
    await message.answer(
        "👥 Выберите администратора для удаления:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("deleteadmin_"))
async def process_admin_deletion(callback: CallbackQuery, state: FSMContext):
    """Обработка удаления администратора"""
    if callback.from_user.id != super_admin_id:
        await callback.message.answer("❌ У вас нет прав для удаления администраторов")
        await state.clear()
        return
        
    admin_id = int(callback.data.split("_")[1])
    
    if await db.delete_admin(admin_id):
        await callback.message.answer(
            "✅ Администратор успешно удален",
            reply_markup=kb.admin_main
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при удалении администратора",
            reply_markup=kb.admin_main
        )
    await state.clear()

class AdminFilter(BaseFilter):
    """Фильтр для проверки прав администратора"""
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        return user_id == super_admin_id or await db.is_admin(user_id)

admin_filter = AdminFilter()

@router.message(Command('admin'))
async def cmd_admin(message: Message):
    """Обработчик команды администратора"""
    user_id = message.from_user.id
    is_super_admin = user_id == super_admin_id
    is_admin = await db.is_admin(user_id)
    
    if is_admin or is_super_admin:
        await message.answer(
            "👋 Добро пожаловать в панель администратора!",
            reply_markup=kb.admin_main
        )
    else:
        await message.answer("❌ У вас нет прав администратора.")

@router.message(admin_filter, F.text == '🚪 Выйти')
async def exit_admin(message: Message):
    """Выход из режима администратора"""
    await message.answer(
        "👋 Вы вышли из режима администратора",
        reply_markup=kb.main
    )

@router.message(admin_filter, F.text == '➕ Добавить категорию')
async def add_category(message: Message, state: FSMContext):
    """Начало процесса добавления категории"""
    await state.set_state(st.AddCategory.name)
    await message.answer("📝 Введите название категории:")

@router.message(admin_filter, st.AddCategory.name)
async def add_category_sure(message: Message, state: FSMContext):
    """Подтверждение добавления категории"""
    await state.update_data(name=message.text)
    await state.set_state(st.AddCategory.confirm)
    await message.answer(
        f"❓ Вы уверены, что хотите добавить категорию '{message.text}'?",
        reply_markup=kb.confirm
    )

@router.callback_query(admin_filter, F.data == 'ok-sure', st.AddCategory.confirm)
async def add_category_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка подтверждения добавления категории"""
    data = await state.get_data()
    await db.add_category(data['name'])
    await callback.message.answer(
        "✅ Категория добавлена",
        reply_markup=kb.admin_main
    )
    await state.clear()

@router.callback_query(admin_filter, F.data == 'cancel-sure', st.AddCategory.confirm)
async def add_category_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления категории"""
    await callback.message.answer(
        "❌ Добавление категории отменено",
        reply_markup=kb.admin_main
    )
    await state.clear()

@router.message(admin_filter, F.text == '➖ Удалить категорию')
async def delete_category_select(message: Message, state: FSMContext):
    """Начало процесса удаления категории"""
    await state.set_state(st.DeleteCategory.select)
    keyboard = await kb.delete_categories()
    await message.answer(
        "📋 Выберите категорию для удаления:",
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

@router.message(admin_filter, F.text == '➕ Добавить товар')
async def add_product(message: Message, state: FSMContext):
    """Начало процесса добавления товара"""
    await state.set_state(st.AddProduct.category)
    keyboard = await kb.categories()
    await message.answer(
        "📋 Выберите категорию для нового товара:",
        reply_markup=keyboard
    )

@router.callback_query(admin_filter, F.data.startswith("category_"), st.AddProduct.category)
async def add_product_name(callback: CallbackQuery, state: FSMContext):
    """Ввод названия нового товара"""
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)
    await state.set_state(st.AddProduct.name)
    await callback.message.answer("📝 Введите название товара:")

@router.message(admin_filter, st.AddProduct.name)
async def add_product_description(message: Message, state: FSMContext):
    """Ввод описания нового товара"""
    await state.update_data(name=message.text)
    await state.set_state(st.AddProduct.description)
    await message.answer("📝 Введите описание товара:")

@router.message(admin_filter, st.AddProduct.description)
async def add_product_price(message: Message, state: FSMContext):
    """Ввод цены нового товара"""
    await state.update_data(description=message.text)
    await state.set_state(st.AddProduct.price)
    await message.answer("💰 Введите цену товара:")

@router.message(admin_filter, st.AddProduct.price)
async def add_product_photo(message: Message, state: FSMContext):
    """Загрузка фото нового товара"""
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(st.AddProduct.photo)
        await message.answer("🖼 Отправьте фото товара:")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену")

@router.message(admin_filter, st.AddProduct.photo, F.photo)
async def add_product_confirm(message: Message, state: FSMContext):
    """Подтверждение добавления товара"""
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo=photo_file_id)
    data = await state.get_data()
    
    await message.answer_photo(
        photo=data['photo'],
        caption=f"📦 Товар: {data['name']}\n"
                f"📝 Описание: {data['description']}\n"
                f"💰 Цена: {data['price']}\n\n"
                f"❓ Подтвердите добавление товара",
        reply_markup=kb.confirm
    )
    await state.set_state(st.AddProduct.confirm)

@router.callback_query(admin_filter, F.data == 'ok-sure', st.AddProduct.confirm)
async def add_product_finish(callback: CallbackQuery, state: FSMContext):
    """Завершение добавления товара"""
    data = await state.get_data()
    
    if await db.add_product(
        category_id=data['category_id'],
        name=data['name'],
        description=data['description'],
        price=data['price'],
        photo=data['photo']
    ):
        await callback.message.answer(
            "✅ Товар успешно добавлен",
            reply_markup=kb.admin_main
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при добавлении товара",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.message(F.text == '➖ Удалить товар')
async def delete_product_select_category(message: Message, state: FSMContext):
    """Начало процесса удаления товара - выбор категории"""
    await state.set_state(st.DeleteProduct.select_category)
    keyboard = await kb.categories()
    await message.answer(
        "📋 Выберите категорию товара для удаления:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("category_"), st.DeleteProduct.select_category)
async def delete_product_select(callback: CallbackQuery, state: FSMContext):
    """Выбор товара для удаления из категории"""
    category_id = int(callback.data.split("_")[1])
    keyboard = await kb.products_by_category(category_id)
    await callback.message.answer(
        "📦 Выберите товар для удаления:",
        reply_markup=keyboard
    )
    await state.set_state(st.DeleteProduct.select)

@router.callback_query(F.data.startswith("product_"), st.DeleteProduct.select)
async def delete_product_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара"""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    
    if product:
        await state.update_data(product_id=product_id)
        await callback.message.answer_photo(
            photo=product.photo,
            caption=f"📦 Товар: {product.name}\n"
                    f"📝 Описание: {product.description}\n"
                    f"💰 Цена: {product.price}\n\n"
                    f"❓ Вы уверены, что хотите удалить этот товар?",
            reply_markup=kb.confirm
        )
        await state.set_state(st.DeleteProduct.confirm)
    else:
        await callback.message.answer(
            "❌ Товар не найден",
            reply_markup=kb.admin_main
        )
        await state.clear()

@router.callback_query(F.data == "ok-sure", st.DeleteProduct.confirm)
async def delete_product_finish(callback: CallbackQuery, state: FSMContext):
    """Завершение удаления товара"""
    data = await state.get_data()
    if await db.delete_product(data['product_id']):
        await callback.message.answer(
            "✅ Товар успешно удален",
            reply_markup=kb.admin_main
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при удалении товара",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.callback_query(F.data == "cancel-sure", st.DeleteProduct.confirm)
async def cancel_delete_product(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления товара"""
    await callback.message.answer(
        "❌ Удаление товара отменено",
        reply_markup=kb.admin_main
    )
    await state.clear()

@router.message(admin_filter, F.text == '✏️ Редактировать товар')
async def edit_product_cmd(message: Message, state: FSMContext):
    """Начало процесса редактирования товара"""
    await state.set_state(st.EditProduct.select_category)
    keyboard = await kb.categories()
    await message.answer(
        "📋 Выберите категорию товара:",
        reply_markup=keyboard
    )

@router.callback_query(admin_filter, F.data.startswith("category_"), st.EditProduct.select_category)
async def edit_product_select(callback: CallbackQuery, state: FSMContext):
    """Выбор товара для редактирования"""
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)
    keyboard = await kb.products_by_category(category_id)
    await callback.message.answer(
        "📦 Выберите товар для редактирования:",
        reply_markup=keyboard
    )
    await state.set_state(st.EditProduct.select_product)

@router.callback_query(admin_filter, F.data.startswith("product_"), st.EditProduct.select_product)
async def edit_product_menu(callback: CallbackQuery, state: FSMContext):
    """Меню редактирования товара"""
    product_id = int(callback.data.split("_")[1])
    await state.update_data(product_id=product_id)
    product = await db.get_product(product_id)
    
    if product:
        await callback.message.answer_photo(
            photo=product.photo,
            caption=f"📦 Товар: {product.name}\n"
                    f"📝 Описание: {product.description}\n"
                    f"💰 Цена: {product.price}\n\n"
                    f"✏️ Выберите, что хотите изменить:",
            reply_markup=kb.edit_product
        )
        await state.set_state(st.EditProduct.select_field)
    else:
        await callback.message.answer(
            "❌ Товар не найден",
            reply_markup=kb.admin_main
        )
        await state.clear()

@router.callback_query(admin_filter, F.data == "edit_name", st.EditProduct.select_field)
async def edit_product_name(callback: CallbackQuery, state: FSMContext):
    """Редактирование названия товара"""
    await callback.message.answer("📝 Введите новое название товара:")
    await state.set_state(st.EditProduct.edit_name)

@router.message(admin_filter, st.EditProduct.edit_name)
async def save_product_name(message: Message, state: FSMContext):
    """Сохранение нового названия товара"""
    data = await state.get_data()
    if await db.update_product_name(data['product_id'], message.text):
        await message.answer(
            "✅ Название товара обновлено",
            reply_markup=kb.admin_main
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении названия",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.callback_query(admin_filter, F.data == "edit_description", st.EditProduct.select_field)
async def edit_product_description(callback: CallbackQuery, state: FSMContext):
    """Редактирование описания товара"""
    await callback.message.answer("📝 Введите новое описание товара:")
    await state.set_state(st.EditProduct.edit_description)

@router.message(admin_filter, st.EditProduct.edit_description)
async def save_product_description(message: Message, state: FSMContext):
    """Сохранение нового описания товара"""
    data = await state.get_data()
    if await db.update_product_description(data['product_id'], message.text):
        await message.answer(
            "✅ Описание товара обновлено",
            reply_markup=kb.admin_main
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении описания",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.callback_query(admin_filter, F.data == "edit_price", st.EditProduct.select_field)
async def edit_product_price(callback: CallbackQuery, state: FSMContext):
    """Редактирование цены товара"""
    await callback.message.answer("💰 Введите новую цену товара:")
    await state.set_state(st.EditProduct.edit_price)

@router.message(admin_filter, st.EditProduct.edit_price)
async def save_product_price(message: Message, state: FSMContext):
    """Сохранение новой цены товара"""
    try:
        price = float(message.text)
        data = await state.get_data()
        if await db.update_product_price(data['product_id'], price):
            await message.answer(
                "✅ Цена товара обновлена",
                reply_markup=kb.admin_main
            )
        else:
            await message.answer(
                "❌ Ошибка при обновлении цены",
                reply_markup=kb.admin_main
            )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену")
        return
    await state.clear()

@router.callback_query(admin_filter, F.data == "edit_photo", st.EditProduct.select_field)
async def edit_product_photo(callback: CallbackQuery, state: FSMContext):
    """Редактирование фото товара"""
    await callback.message.answer("🖼 Отправьте новое фото товара:")
    await state.set_state(st.EditProduct.edit_photo)

@router.message(admin_filter, st.EditProduct.edit_photo, F.photo)
async def save_product_photo(message: Message, state: FSMContext):
    """Сохранение нового фото товара"""
    photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    if await db.update_product_photo(data['product_id'], photo_file_id):
        product = await db.get_product(data['product_id'])
        await message.answer_photo(
            photo=product.photo,
            caption="✅ Фото товара обновлено",
            reply_markup=kb.admin_main
        )
    else:
        await message.answer(
            "❌ Ошибка при обновлении фото",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.callback_query(admin_filter, F.data == "edit_category", st.EditProduct.select_field)
async def edit_product_category(callback: CallbackQuery, state: FSMContext):
    """Редактирование категории товара"""
    keyboard = await kb.categories()
    await callback.message.answer(
        "📋 Выберите новую категорию для товара:",
        reply_markup=keyboard
    )
    await state.set_state(st.EditProduct.edit_category)

@router.callback_query(admin_filter, F.data.startswith("category_"), st.EditProduct.edit_category)
async def save_product_category(callback: CallbackQuery, state: FSMContext):
    """Сохранение новой категории товара"""
    category_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    if await db.update_product_category(data['product_id'], category_id):
        await callback.message.answer(
            "✅ Категория товара обновлена",
            reply_markup=kb.admin_main
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при обновлении категории",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.callback_query(admin_filter, F.data == "back_to_menu")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню администратора"""
    await state.clear()
    await callback.message.answer(
        "👋 Добро пожаловать в панель администратора!",
        reply_markup=kb.admin_main
    )

@router.callback_query(F.data.in_({'cancel-sure', 'cancel_delete'}))
async def cancel_delete_action(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Действие отменено", reply_markup=kb.admin_main)
    await state.clear()

@router.callback_query(F.data.startswith('product_'))
async def show_product(callback: CallbackQuery):
    try:
        product_id = int(callback.data.split('_')[1])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.message.answer("Товар не найден")
            return
            
        text = (
            f"📦 {product.name}\n"
            f"📝 {product.description}\n"
            f"💰 {product.price}₽"
        )
        
        if product.photo_id:
            await callback.message.answer_photo(
                photo=product.photo_id,
                caption=text,
                reply_markup=kb.product_actions(product_id)
            )
        else:
            await callback.message.answer(
                text,
                reply_markup=kb.product_actions(product_id)
            )
            
    except Exception as e:
        logging.error(f"Ошибка при показе товара: {e}")
        await callback.message.answer("Произошла ошибка при показе товара")