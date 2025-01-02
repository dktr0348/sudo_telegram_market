from aiogram import F
from aiogram import Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart, BaseFilter
from src.config import admin_ids, super_admin_id, Config
from src.database.database import Database
import src.state as st
import src.keyboards as kb
import src.database.requests as db
from aiogram.fsm.context import FSMContext
import logging
from ..database.models import StarsTransaction  # Добавляем импорт модели

router = Router()

async def check_admin(message: Message) -> bool:
    """Проверка является ли пользователь администратором"""
    if message.from_user.id not in Config.admin_ids:
        await message.answer("⛔️ У вас нет прав администратора")
        return False
    return True

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

@router.message(admin_filter, F.text == '✏️ Редактировать товар')
async def edit_product_cmd(message: Message, state: FSMContext):
    """Начало процесса редактирования товара"""
    await state.set_state(st.EditProduct.select_category)
    keyboard = await kb.admin_categories_kb()
    await message.answer(
        "📋 Выберите категорию товара:",
        reply_markup=keyboard
    )

@router.callback_query(admin_filter, F.data.startswith("admin_category_"), st.EditProduct.select_category)
async def edit_product_select(callback: CallbackQuery, state: FSMContext):
    """Выбор товара для редактирования из категории"""
    category_id = int(callback.data.split('_')[2])
    await state.update_data(category_id=category_id)
    
    keyboard = await kb.admin_products_by_category(category_id)
    if keyboard:
        await callback.message.edit_text(
            "📦 Выберите товар для редактирования:",
            reply_markup=keyboard
        )
        await state.set_state(st.EditProduct.select_product)
    else:
        await callback.message.edit_text(
            "❌ В этой категории нет товаров",
            reply_markup=await kb.admin_categories_kb()
        )
        await state.clear()

@router.callback_query(admin_filter, F.data.startswith("edit_product_"), st.EditProduct.select_product)
async def edit_product_select_field(callback: CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования"""
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    
    product = await db.get_product_by_id(product_id)
    if product:
        text = (
            f"📦 Товар: {product.name}\n"
            f"💰 Цена: {product.price}₽\n"
            f"🔢 Количество: {product.quantity}\n"
            f"📝 Описание: {product.description}\n\n"
            "Выберите, что хотите отредактировать:"
        )
        
        if product.photo_id:
            await callback.message.delete()  # Удаляем предыдущее сообщение
            await callback.message.answer_photo(
                photo=product.photo_id,
                caption=text + "\nВыберите, что хотите отредактировать:",
                reply_markup=kb.edit_product
            )
        else:
            await callback.message.edit_text(
                text + "\nВыберите, что хотите отредактировать:",
                reply_markup=kb.edit_product
            )
        await state.set_state(st.EditProduct.select_field)
    else:
        await callback.message.edit_text(
            "❌ Товар не найден",
            reply_markup=kb.admin_main
        )
        await state.clear()

async def show_edit_menu(message: Message, state: FSMContext, success_message: str = ""):
    """Показать меню редактирования после изменения"""
    data = await state.get_data()
    product = await db.get_product_by_id(data['product_id'])
    
    if product:
        text = (
            f"{success_message}\n\n" if success_message else ""
            f"📦 Товар: {product.name}\n"
                    f"📝 Описание: {product.description}\n"
            f"💰 Цена: {product.price}₽\n"
            f"🔢 Количество: {product.quantity}\n\n"
            "Выберите, что хотите отредактировать:"
        )
        
        if product.photo_id:
            await message.answer_photo(
                photo=product.photo_id,
                caption=text,
                reply_markup=kb.edit_product
            )
        else:
            await message.answer(
                text,
            reply_markup=kb.edit_product
        )
        await state.set_state(st.EditProduct.select_field)
    else:
        await message.answer(
            "❌ Товар не найден",
            reply_markup=kb.admin_main
        )
        await state.clear()

@router.message(admin_filter, st.EditProduct.edit_name)
async def save_product_name(message: Message, state: FSMContext):
    """Сохранение нового названия товара"""
    data = await state.get_data()
    if await db.edit_product(data['product_id'], name=message.text):
        await show_edit_menu(message, state, "✅ Название товара обновлено")
    else:
        await message.answer("❌ Ошибка при обновлении названия")

@router.message(admin_filter, st.EditProduct.edit_description)
async def save_product_description(message: Message, state: FSMContext):
    data = await state.get_data()
    if await db.edit_product(data['product_id'], description=message.text):
        await show_edit_menu(message, state, "✅ Описание товара обновлено")
    else:
        await message.answer("❌ Ошибка при обновлении описания")

@router.message(admin_filter, st.EditProduct.edit_price)
async def save_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        data = await state.get_data()
        if await db.edit_product(data['product_id'], price=price):
            await show_edit_menu(message, state, "✅ Цена товара обновлена")
        else:
            await message.answer("❌ Ошибка при обновлении цены")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену")

@router.message(admin_filter, st.EditProduct.edit_quantity)
async def save_product_quantity(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
        if quantity < 0:
            await message.answer("❌ Количество не может быть отрицательным")
            return
        
        data = await state.get_data()
        if await db.edit_product(data['product_id'], quantity=quantity):
            await show_edit_menu(message, state, "✅ Количество товара обновлено")
        else:
            await message.answer("❌ Ошибка при обновлении количества")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число")
        return
    await state.clear()

@router.callback_query(admin_filter, F.data == "edit_field_photo", st.EditProduct.select_field)
async def edit_product_photo(callback: CallbackQuery, state: FSMContext):
    """Редактирование фото товара"""
    await callback.message.answer(
        "🖼 Отправьте новое фото товара:",
        reply_markup=kb.cancel_keyboard
    )
    await state.set_state(st.EditProduct.edit_photo)

@router.message(admin_filter, st.EditProduct.edit_photo, F.photo)
async def save_product_photo(message: Message, state: FSMContext):
    """Сохранение нового фото товара"""
    try:
        photo_id = message.photo[-1].file_id
        data = await state.get_data()
        if await db.edit_product(data['product_id'], photo_id=photo_id):
            await show_edit_menu(message, state, "✅ Фото товара обновлено")
        else:
            await message.answer(
                "❌ Ошибка при обновлении фото",
                reply_markup=kb.edit_product
            )
    except Exception as e:
        logging.error(f"Ошибка при обновлении фото: {e}")
        await message.answer(
            "❌ Произошла ошибка при обновлении фото",
            reply_markup=kb.edit_product
        )

@router.message(F.text == '➖ Удалить товар')
async def delete_product_start(message: Message, state: FSMContext):
    """Начало процесса удаления товара"""
    await state.set_state(st.DeleteProduct.select_category)
    keyboard = await kb.admin_categories_kb()
    await message.answer(
        "📋 Выберите категорию товара для удаления:",
        reply_markup=keyboard
    )

@router.callback_query(admin_filter, F.data.startswith("admin_category_"), st.DeleteProduct.select_category)
async def delete_product_select_category(callback: CallbackQuery, state: FSMContext):
    """Выбор категории для удаления товара"""
    category_id = int(callback.data.split('_')[2])
    await state.update_data(category_id=category_id)
    
    keyboard = await kb.admin_products_by_category_kb(category_id)
    if keyboard:
        await callback.message.edit_text(
            "📦 Выберите товар для удаления:",
            reply_markup=keyboard
        )
        await state.set_state(st.DeleteProduct.select_product)
    else:
        await callback.message.edit_text(
            "❌ В этой категории нет товаров",
            reply_markup=await kb.admin_categories_kb()
        )
        await state.clear()

@router.callback_query(admin_filter, F.data.startswith("admin_product_"), st.DeleteProduct.select_product)
async def delete_product_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара"""
    product_id = int(callback.data.split('_')[2])
    await state.update_data(product_id=product_id)
    
    product = await db.get_product_by_id(product_id)
    if product:
        text = (
            f"❗️ Вы действительно хотите удалить товар?\n\n"
            f"📦 {product.name}\n"
            f"💰 {product.price}₽\n"
            f"📝 {product.description}"
        )
        
        if product.photo_id:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=product.photo_id,
                caption=text,
                reply_markup=kb.confirm
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=kb.confirm
            )
        await state.set_state(st.DeleteProduct.confirm)
    else:
        await callback.message.edit_text(
            "❌ Товар не найден",
            reply_markup=kb.admin_main
        )
        await state.clear()

@router.callback_query(admin_filter, F.data == "ok-sure", st.DeleteProduct.confirm)
async def delete_product_final(callback: CallbackQuery, state: FSMContext):
    """Окончательное удаление товара"""
    data = await state.get_data()
    product_id = data.get('product_id')
    
    if await db.delete_product(product_id):
        # Отправляем новое сообщение вместо редактирования
        await callback.message.delete()  # Удаляем старое сообщение
        await callback.message.answer(
            "✅ Товар успешно удален",
            reply_markup=kb.admin_main
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "❌ Ошибка при удалении товара",
            reply_markup=kb.admin_main
        )
    await state.clear()

@router.callback_query(admin_filter, F.data == "cancel-sure", st.DeleteProduct.confirm)
async def cancel_delete_product(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления товара"""
    # Отправляем новое сообщение вместо редактирования
    await callback.message.delete()
    await callback.message.answer(
        "❌ Удаление товара отменено",
        reply_markup=kb.admin_main
    )
    # Отправляем дополнительное сообщение с подтверждением
    await callback.answer("❌ Удаление отменено!", show_alert=True)
    await state.clear()

@router.callback_query(F.data == "back_to_admin_categories")
async def back_to_admin_categories(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку категорий (админская версия)"""
    await state.set_state(st.EditProduct.select_category)
    keyboard = await kb.admin_categories_kb()
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "📋 Выберите категорию:",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            "📋 Выберите категорию:",
            reply_markup=keyboard
        )

@router.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в админ меню"""
    await state.clear()
    
    # Создаем инлайн клавиатуру для возврата в админ меню
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В админ меню", callback_data="admin_menu")]
    ])
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "👑 Панель администратора",
            reply_markup=admin_kb
        )
    else:
        await callback.message.edit_text(
            "👑 Панель администратора",
            reply_markup=admin_kb
        )

# Добавим обработчик для кнопки возврата в админ меню
@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery):
    """Показ админ меню"""
    await callback.message.answer(
        "👑 Панель администратора",
        reply_markup=kb.admin_main
    )
    # Удаляем предыдущее сообщение с инлайн кнопкой
    await callback.message.delete()

@router.callback_query(F.data.startswith("product_"))
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

@router.callback_query(admin_filter, F.data == "edit_field_quantity", st.EditProduct.select_field)
async def edit_product_quantity(callback: CallbackQuery, state: FSMContext):
    """Редактирование количества товара"""
    await callback.message.answer("🔢 Введите новое количество товара:")
    await state.set_state(st.EditProduct.edit_quantity)

@router.message(admin_filter, st.EditProduct.edit_quantity)
async def save_product_quantity(message: Message, state: FSMContext):
    """Сохранение нового количества товара"""
    try:
        quantity = int(message.text)
        if quantity < 0:
            await message.answer("❌ Количество не может быть отрицательным")
            return
            
        data = await state.get_data()
        if await db.edit_product(data['product_id'], quantity=quantity):
            await show_edit_menu(message, state, "✅ Количество товара обновлено")
        else:
            await message.answer("❌ Ошибка при обновлении количества")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число")
        return
    await state.clear()

@router.callback_query(admin_filter, F.data == "edit_field_category", st.EditProduct.select_field)
async def edit_product_category(callback: CallbackQuery, state: FSMContext):
    """Редактирование категории товара"""
    product_id = (await state.get_data()).get('product_id')
    if not product_id:
        await callback.message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return
        
    await state.update_data(product_id=product_id)
    await state.set_state(st.EditProduct.edit_category)
    
    keyboard = await kb.admin_categories_kb()
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "📋 Выберите новую категорию для товара:",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            "📋 Выберите новую категорию для товара:",
            reply_markup=keyboard
        )

@router.callback_query(admin_filter, F.data.startswith("admin_category_"), st.EditProduct.edit_category)
async def save_product_category(callback: CallbackQuery, state: FSMContext):
    """Сохранение новой категории товара"""
    try:
        category_id = int(callback.data.split("_")[2])
        data = await state.get_data()
        product_id = data.get('product_id')
        
        if not product_id:
            await callback.message.edit_text(
                "❌ Ошибка: товар не найден",
                reply_markup=kb.admin_main
            )
            await state.clear()
            return
            
        if await db.edit_product(product_id, category_id=category_id):
            await show_edit_menu(callback.message, state, "✅ Категория товара обновлена")
        else:
            await callback.message.edit_text(
                "❌ Ошибка при обновлении категории",
                reply_markup=kb.admin_main
            )
    except Exception as e:
        logging.error(f"Ошибка при обновлении категории: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при обновлении категории",
            reply_markup=kb.admin_main
        )

# Добавим обработчик для возврата в меню редактирования
@router.callback_query(F.data == "back_to_edit_menu")
async def back_to_edit_menu_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню редактирования"""
    data = await state.get_data()
    if data.get('product_id'):
        await show_edit_menu(callback.message, state, "")
    else:
        await callback.message.edit_text(
            "Вернуться к редактированию не удалось",
            reply_markup=kb.admin_main
        )
        await state.clear()

@router.callback_query(admin_filter, F.data == "edit_field_name", st.EditProduct.select_field)
async def edit_product_name(callback: CallbackQuery, state: FSMContext):
    """Редактирование названия товара"""
    await callback.message.answer(
        "📝 Введите новое название товара:",
        reply_markup=kb.cancel_keyboard
    )
    await state.set_state(st.EditProduct.edit_name)

@router.callback_query(admin_filter, F.data == "edit_field_description", st.EditProduct.select_field)
async def edit_product_description(callback: CallbackQuery, state: FSMContext):
    """Редактирование описания товара"""
    await callback.message.answer(
        "📝 Введите новое описание товара:",
        reply_markup=kb.cancel_keyboard
    )
    await state.set_state(st.EditProduct.edit_description)

@router.callback_query(admin_filter, F.data == "edit_field_price", st.EditProduct.select_field)
async def edit_product_price(callback: CallbackQuery, state: FSMContext):
    """Редактирование цены товара"""
    await callback.message.answer(
        "💰 Введите новую цену товара:",
        reply_markup=kb.cancel_keyboard
    )
    await state.set_state(st.EditProduct.edit_price)

@router.callback_query(admin_filter, F.data == "edit_field_photo", st.EditProduct.select_field)
async def edit_product_photo(callback: CallbackQuery, state: FSMContext):
    """Редактирование фото товара"""
    await callback.message.answer(
        "🖼 Отправьте новое фото товара:",
        reply_markup=kb.cancel_keyboard
    )
    await state.set_state(st.EditProduct.edit_photo)

@router.message(admin_filter, st.EditProduct.edit_photo, F.photo)
async def save_product_photo(message: Message, state: FSMContext):
    """Сохранение нового фото товара"""
    try:
        photo_id = message.photo[-1].file_id
        data = await state.get_data()
        if await db.edit_product(data['product_id'], photo_id=photo_id):
            await show_edit_menu(message, state, "✅ Фото товара обновлено")
        else:
            await message.answer(
                "❌ Ошибка при обновлении фото",
                reply_markup=kb.edit_product
            )
    except Exception as e:
        logging.error(f"Ошибка при обновлении фото: {e}")
        await message.answer(
            "❌ Произошла ошибка при обновлении фото",
            reply_markup=kb.edit_product
        )

@router.callback_query(admin_filter, F.data == "ok-sure", st.AddProduct.confirm)
async def add_product_finish(callback: CallbackQuery, state: FSMContext):
    """Подтверждение добавления товара"""
    data = await state.get_data()
    
    try:
        if await db.add_product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            category_id=data['category_id'],
            photo_id=data.get('photo')  # Используем get() тк как фото может отсутствовать
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
    except Exception as e:
        logging.error(f"Ошибка при добавлении товара: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при добавлении товара",
            reply_markup=kb.admin_main
        )
    finally:
        await state.clear()

@router.callback_query(admin_filter, F.data == "cancel-sure", st.AddProduct.confirm)
async def add_product_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления товара"""
    await state.clear()
    await callback.message.answer(
        "❌ Добавление товара отменено",
        reply_markup=kb.admin_main
    )

@router.message(F.text == '➕ Добавить товар')
async def add_product_start(message: Message, state: FSMContext):
    """Начало добавления товара"""
    await state.set_state(st.AddProduct.category)
    keyboard = await kb.admin_categories_kb()
    await message.answer(
        "📋 Выберите категорию для нового товара:",
        reply_markup=keyboard
    )

@router.callback_query(admin_filter, F.data.startswith("admin_category_"), st.AddProduct.category)
async def add_product_name(callback: CallbackQuery, state: FSMContext):
    """Выбор категории при добавлении товара"""
    category_id = int(callback.data.split('_')[2])
    await state.update_data(category_id=category_id)
    await state.set_state(st.AddProduct.name)
    await callback.message.answer(
        "📝 Введите название товара:",
        reply_markup=kb.cancel_keyboard
    )

@router.message(admin_filter, st.AddProduct.name)
async def add_product_description(message: Message, state: FSMContext):
    """Ввод описания товара"""
    await state.update_data(name=message.text)
    await state.set_state(st.AddProduct.description)
    await message.answer(
        "📝 Введите описание товара:",
        reply_markup=kb.cancel_keyboard
    )

@router.message(admin_filter, st.AddProduct.description)
async def add_product_price(message: Message, state: FSMContext):
    """Ввод цены товара"""
    await state.update_data(description=message.text)
    await state.set_state(st.AddProduct.price)
    await message.answer(
        "💰 Введите цену товара:",
        reply_markup=kb.cancel_keyboard
    )

@router.message(admin_filter, st.AddProduct.price)
async def add_product_photo(message: Message, state: FSMContext):
    """Запрос фото товара"""
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(st.AddProduct.photo)
        await message.answer(
            "📷 Отправьте фото товара (или нажмите «Пропустить фото»):",
            reply_markup=kb.skip_photo_kb
            )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену")

@router.message(F.text == "⏩ Пропустить фото", st.AddProduct.photo)
async def skip_product_photo(message: Message, state: FSMContext):
    """Пропуск добавления фото"""
    await state.update_data(photo=None)
    data = await state.get_data()
    await confirm_product_adding(message, state, data)

@router.message(admin_filter, st.AddProduct.photo, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    """Обработка фото товара"""
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    data = await state.get_data()
    await confirm_product_adding(message, state, data)

async def confirm_product_adding(message: Message, state: FSMContext, data: dict):
    """Подтверждение добавления товара"""
    text = (
        f"📦 Название: {data['name']}\n"
        f"📝 Описание: {data['description']}\n"
        f"💰 Цена: {data['price']}₽\n"
        f"🖼 Фото: {'Добавлено' if data.get('photo') else 'Нет'}\n\n"
        "Подтвердите добавление товара:"
    )
    # Используем инлайн клавиатуру для подтверждения
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="ok-sure"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel-sure")
        ]
    ])
    await message.answer(text, reply_markup=confirm_kb)
    await state.set_state(st.AddProduct.confirm)

# Добавим общий обработчик отмены
@router.message(F.text == "❌ Отменить")
async def cancel_any_state(message: Message, state: FSMContext):
    """Отмена любого действия"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "Действие отменено",
            reply_markup=kb.admin_main
        )

@router.message(F.text == "❌ Отменить", st.DeleteAdmin.confirm)
async def cancel_delete_admin(message: Message, state: FSMContext):
    """Отмена удаления администратора"""
    await state.clear()
    await message.answer(
        "❌ Удаление администратора отменено",
        reply_markup=kb.admin_main
    )

@router.callback_query(F.data == "back_to_admin_menu", st.EditProduct.select_field)
async def back_to_admin_menu_from_edit(callback: CallbackQuery, state: FSMContext):
    """Возврат в админ меню из редактирования товара"""
    await state.clear()
    await callback.message.edit_text(
        "👑 Панель администратора",
        reply_markup=kb.admin_main
    )

@router.callback_query(F.data == "back_to_category_products")
async def back_to_category_products(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку товаров в категории"""
    data = await state.get_data()
    category_id = data.get('category_id')
    
    if category_id:
        keyboard = await kb.admin_products_by_category_kb(category_id)
        if keyboard:
            if callback.message.photo:
                await callback.message.delete()
                await callback.message.answer(
                    "📦 Выберите товар:",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    "📦 Выберите товар:",
                    reply_markup=keyboard
                )
            await state.set_state(st.EditProduct.select_product)
        else:
            await callback.message.edit_text(
                "❌ В этой категории нет товаров",
                reply_markup=kb.admin_main
            )
            await state.clear()
    else:
        await callback.message.edit_text(
            "❌ Ошибка: категория не найдена",
            reply_markup=kb.admin_main
        )
        await state.clear()

@router.message(Command("stars_history"))
async def show_stars_history(message: Message):
    """Показать историю транзакций Stars"""
    try:
        # Проверяем права через существующую систему и super_admin
        admins = await db.get_admins()
        if message.from_user.id not in [admin.user_id for admin in admins] and message.from_user.id != super_admin_id:
            await message.answer("⛔️ У вас нет прав администратора")
            return
            
        # Получаем историю транзакций
        transactions = await db.get_stars_transactions(limit=20)
        
        if not transactions:
            await message.answer("История транзакций Stars пуста")
            return
            
        # Формируем текст отчета
        report = "📊 История транзакций Stars:\n\n"
        for tx in transactions:
            status_emoji = "✅" if tx.status == "completed" else "❌"
            report += (
                f"{status_emoji} Заказ #{tx.order_id}\n"
                f"👤 User ID: {tx.user_id}\n"
                f"⭐ Stars: {tx.stars_amount}\n"
                f"💰 Сумма: {tx.amount_rub}₽\n"
                f"📅 Дата: {tx.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"📝 Статус: {tx.status}\n\n"
            )
            
        await message.answer(report)
        
    except Exception as e:
        logging.error(f"Ошибка при показе истории Stars: {e}")
        await message.answer("❌ Ошибка при получении истории транзакций")

