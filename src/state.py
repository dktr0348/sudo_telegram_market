from aiogram.fsm.state import State, StatesGroup

class Register(StatesGroup):
    name = State()
    contact = State()
    email = State()
    location = State()
    age = State()
    photo = State()
    confirm = State()

class EditProfile(StatesGroup):
    edit_name = State()
    edit_contact = State()
    edit_email = State()
    edit_location = State()
    edit_age = State()
    edit_photo = State()
    confirm = State()

class AddCategory(StatesGroup):
    name = State()
    confirm = State()
   

class DeleteCategory(StatesGroup):
    select = State()
    confirm = State()
   
class AddProduct(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    photo = State()
    confirm = State()
   
class DeleteProduct(StatesGroup):
    select_category = State()
    select = State()
    confirm = State()

class AddAdmin(StatesGroup):
    name = State()
    confirm = State()

class DeleteAdmin(StatesGroup):
    select = State()
    confirm = State()

class EditProduct(StatesGroup):
    select_category = State()
    select_product = State()
    select_field = State()
    edit_name = State()
    edit_description = State()
    edit_price = State()
    edit_photo = State()
    edit_category = State()
    edit_quantity = State()
    confirm = State()
