from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    fcs = State()
    company = State()
    text = State()
    dialog = State()
