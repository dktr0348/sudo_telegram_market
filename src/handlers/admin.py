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
    async def __call__(self, message: Message | CallbackQuery) -> bool:
        if isinstance(message, Message):
            user_id = message.from_user.id
        else:
            user_id = message.from_user.id
        is_super_admin = user_id == super_admin_id
        logging.info(f"Проверка прав супер-администратора для пользователя {user_id}: {is_super_admin}")
        return is_super_admin

super_admin_filter = SuperAdminFilter()

@router.message(Command('superadmin'))
async def super_admin_cmd(message: Message):
    if message.from_user.id == super_admin_id:
        await message.answer("Вы супер-администратор", reply_markup=kb.admin_main)
    else:
        await message.answer("У вас нет прав супер-администратора")

@router.message(F.text == 'Добавить админа')
async def add_admin_cmd(message: Message, state: FSMContext):
    if message.from_user.id != super_admin_id:
        await message.answer("У вас нет прав для добавления администраторов")
        return
        
    await state.set_state(st.AddAdmin.name)
    await message.answer(
        "Введите ID пользователя для добавления в администраторы:",
        reply_markup=kb.admin_main
    )

@router.message(st.AddAdmin.name)
async def add_admin_confirm(message: Message, state: FSMContext):
    if message.from_user.id != super_admin_id:
        await message.answer("У вас нет прав для добавления администраторов")
        await state.clear()
        return
        
    try:
        admin_id = int(message.text)
        await state.update_data(admin_id=admin_id)
        await state.set_state(st.AddAdmin.confirm)
        await message.answer(
            f"Вы уверены, что хотите добавить пользователя {admin_id} в администраторы?",
            reply_markup=kb.confirm
        )
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректный ID пользователя (целое число)",
            reply_markup=kb.admin_main
        )

@router.callback_query(F.data == 'ok-sure', st.AddAdmin.confirm)
async def add_admin_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != super_admin_id:
        await callback.message.answer("У вас нет прав для добавления администраторов")
        await state.clear()
        return
        
    try:
        data = await state.get_data()
        admin_id = data['admin_id']
        
        if await db.add_admin(admin_id):
            await callback.message.answer(
                f"Пользователь {admin_id} добавлен в администраторы",
                reply_markup=kb.admin_main
            )
        else:
            await callback.message.answer(
                "Ошибка при добавлении администратора",
                reply_markup=kb.admin_main
            )
    except Exception as e:
        logging.error(f"Ошибка при добавлении администратора: {e}")
        await callback.message.answer(
            "Произошла ошибка при добавлении администратора",
            reply_markup=kb.admin_main
        )
    finally:
        await state.clear()

@router.message(F.text == 'Удалить админа')
async def delete_admin_cmd(message: Message, state: FSMContext):
    if message.from_user.id != super_admin_id:
        await message.answer("У вас нет прав для удаления администраторов")
        return
        
    await state.set_state(st.DeleteAdmin.select)
    keyboard = await kb.delete_admins()
    await message.answer(
        "Выберите администратора для удаления:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("deleteadmin_"))
async def process_admin_deletion(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != super_admin_id:
        await callback.message.answer("У вас нет прав для удаления администраторов")
        await state.clear()
        return
        
    try:
        admin_id = int(callback.data.split("_")[1])
        logging.info(f"Попытка удаления администратора {admin_id}")
        
        if await db.delete_admin(admin_id):
            await callback.message.answer(
                "Администратор успешно удален",
                reply_markup=kb.admin_main
            )
            logging.info(f"Администратор {admin_id} успешно удален")
        else:
            await callback.message.answer(
                "Ошибка при удалении администратора",
                reply_markup=kb.admin_main
            )
            logging.error(f"Ошибка при удалении администратора {admin_id}")
    except Exception as e:
        logging.error(f"Ошибка при удалении администратора: {e}")
        await callback.message.answer(
            "Произошла ошибка при удалении администратора",
            reply_markup=kb.admin_main
        )
    finally:
        await state.clear()


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        is_super_admin = user_id == super_admin_id
        is_admin_result = await db.is_admin(user_id)
        logging.info(f"Проверка прав администратора для пользователя {user_id}: admin={is_admin_result}, super_admin={is_super_admin}")
        return is_admin_result or is_super_admin

# Создаем экземпляр фильтра
admin_filter = AdminFilter()

@router.message(Command('admin'))
async def cmd_admin(message: Message):
    user_id = message.from_user.id
    is_super_admin = user_id == super_admin_id
    is_admin = await db.is_admin(user_id)
    
    if is_admin or is_super_admin:
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
async def add_product_photo(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(st.AddProduct.photo)
        await message.answer(
            "Отправьте фотографию товара или нажмите 'Пропустить' для товара без фото:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Пропустить")]],
                resize_keyboard=True
            )
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену (число)")

@router.message(admin_filter, st.AddProduct.photo)
async def add_product_confirm(message: Message, state: FSMContext):
    if not message.photo and message.text != "Пропустить":
        await message.answer("Пожалуйста, отправьте фото или нажмите 'Пропустить'")
        return

    if message.text == "Пропустить":
        await state.update_data(photo_id=None)
    elif message.photo:
        await state.update_data(photo_id=message.photo[-1].file_id)
    
    data = await state.get_data()
    photo_text = "Без фото" if data.get('photo_id') is None else "С фото"
    
    await state.set_state(st.AddProduct.confirm)
    
    confirmation_text = (
        f"Вы уверены, что хотите добавить этот товар?\n\n"
        f"Название: {data['name']}\n"
        f"Описание: {data['description']}\n"
        f"Цена: {data['price']}₽\n"
        f"Фото: {photo_text}"
    )
    
    if data.get('photo_id'):
        await message.answer_photo(
            photo=data['photo_id'],
            caption=confirmation_text,
            reply_markup=kb.confirm
        )
    else:
        await message.answer(
            confirmation_text,
            reply_markup=kb.confirm
        )

@router.callback_query(admin_filter, F.data == 'ok-sure', st.AddProduct.confirm)
async def add_product_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product = await db.add_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        category_id=data['category_id'],
        photo_id=data.get('photo_id')
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

@router.message(admin_filter, F.text == 'Редактировать товар')
async def edit_product_cmd(message: Message, state: FSMContext):
    await state.set_state(st.EditProduct.select)
    keyboard = await kb.edit_product_kb()
    if keyboard:
        await message.answer(
            "Выберите товар для редактирования:",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "Нет доступных товаров для редактирования",
            reply_markup=kb.admin_main
        )

@router.callback_query(admin_filter, F.data.startswith('edit_product_'))
async def process_product_selection(callback: CallbackQuery, state: FSMContext):
    try:
        product_id = int(callback.data.split('_')[2])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.message.answer(
                "Товар не найден",
                reply_markup=kb.admin_main
            )
            return
            
        await state.update_data(product_id=product_id)
        await state.set_state(st.EditProduct.select_field)
        
        await callback.message.answer(
            f"Выберите, что хотите изменить в товаре '{product.name}':",
            reply_markup=kb.edit_product_fields
        )
    except Exception as e:
        logging.error(f"Ошибка при выборе товара: {e}")
        await callback.message.answer(
            "Ошибка при выборе товара",
            reply_markup=kb.admin_main
        )
        await state.clear()

@router.callback_query(admin_filter, F.data.startswith('edit_field_'))
async def process_field_selection(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split('_')[2]
    await state.update_data(edit_field=field)
    
    messages = {
        'name': 'Введите новое название товара:',
        'description': 'Введите новое описание товара:',
        'price': 'Введите новую цену товара:',
        'category': 'Выберите новую категорию товара:',
        'photo': 'Отправьте новое фото товара или нажмите "Удалить фото":'
    }
    
    states = {
        'name': st.EditProduct.edit_name,
        'description': st.EditProduct.edit_description,
        'price': st.EditProduct.edit_price,
        'category': st.EditProduct.edit_category,
        'photo': st.EditProduct.edit_photo
    }
    
    if field == 'category':
        keyboard = await kb.admin_categories()
        if not keyboard:
            await callback.message.answer(
                "Нет доступных категорий",
                reply_markup=kb.admin_main
            )
            return
    elif field == 'photo':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Удалить фото")]],
            resize_keyboard=True
        )
    else:
        keyboard = kb.cancel_kb
    
    await state.set_state(states[field])
    await callback.message.answer(messages[field], reply_markup=keyboard)

@router.message(admin_filter, st.EditProduct.edit_name)
async def process_edit_name(message: Message, state: FSMContext):
    await state.update_data(new_value=message.text)
    await confirm_edit(message, state)

@router.message(admin_filter, st.EditProduct.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    await state.update_data(new_value=message.text)
    await confirm_edit(message, state)

@router.message(admin_filter, st.EditProduct.edit_price)
async def process_edit_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(new_value=price)
        await confirm_edit(message, state)
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректную цену (число)",
            reply_markup=kb.cancel_kb
        )

@router.callback_query(admin_filter, st.EditProduct.edit_category)
async def process_edit_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split('_')[1])
    await state.update_data(new_value=category_id)
    await confirm_edit(callback.message, state)

@router.message(admin_filter, st.EditProduct.edit_photo)
async def process_edit_photo(message: Message, state: FSMContext):
    if message.text == "Удалить фото":
        await state.update_data(new_value=None)
        await confirm_edit(message, state)
    elif message.photo:
        await state.update_data(new_value=message.photo[-1].file_id)
        await confirm_edit(message, state)
    else:
        await message.answer(
            "Пожалуйста, отправьте новое фото или нажмите 'Удалить фото'",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Удалить фото")]],
                resize_keyboard=True
            )
        )

async def confirm_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data['edit_field']
    new_value = data['new_value']
    product = await db.get_product_by_id(data['product_id'])
    
    field_names = {
        'name': 'название',
        'description': 'описание',
        'price': 'цену',
        'category': 'категорию',
        'photo': 'фото'
    }
    
    await state.set_state(st.EditProduct.confirm)
    await message.answer(
        f"Вы хотите изменить {field_names[field]} товара '{product.name}' на '{new_value}'?",
        reply_markup=kb.confirm
    )

@router.callback_query(admin_filter, F.data == 'ok-sure', st.EditProduct.confirm)
async def save_product_changes(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        field = data['edit_field']
        new_value = data['new_value']
        product_id = data['product_id']
        
        if await db.edit_product(product_id, **{field: new_value}):
            await callback.message.answer(
                "Товар успешно отредактирован",
                reply_markup=kb.admin_main
            )
        else:
            await callback.message.answer(
                "Ошибка при редактировании товара",
                reply_markup=kb.admin_main
            )
    except Exception as e:
        logging.error(f"Ошибка при сохранении изменений: {e}")
        await callback.message.answer(
            "Произошла ошибка при сохранении изменений",
            reply_markup=kb.admin_main
        )
    finally:
        await state.clear()

@router.callback_query(F.data == 'cancel_edit')
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Редактирование отменено",
        reply_markup=kb.admin_main
    )

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