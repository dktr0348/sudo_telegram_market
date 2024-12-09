from aiogram.fsm.state import State, StatesGroup

class Register(StatesGroup):
    name = State()
    contact = State()
    email = State()
    location = State()
    age = State()
    photo = State()
    confirm = State() 