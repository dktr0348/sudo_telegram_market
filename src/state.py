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