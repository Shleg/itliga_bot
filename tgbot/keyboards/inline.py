from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.keyboards.callback_data import UserAppCallback, ShowAppInfo, CompletedCommunication, BackInWork, \
    GradeCallback


async def menu_kb(export):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Создать заявку", callback_data="create_application")
    keyboard.button(text="Заявки в работе", callback_data=UserAppCallback(current_idx=0, method='work'))
    keyboard.button(text="Закрытые заявки", callback_data=UserAppCallback(current_idx=0, method='closed'))
    if export:
        keyboard.button(text="Выгрузка статистики Exel", callback_data="export_exel_user")
    keyboard.button(text="Поддержка", callback_data="support")
    return keyboard.adjust(1).as_markup()


async def first_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Продолжить', callback_data="back_to_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()


async def back_to_manu_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='🔙 Назад', callback_data="back_to_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()


async def back_to_manu_2_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='В главное меню', callback_data="back_to_menu")
    keyboard.adjust(1)
    return keyboard.as_markup()


async def accept_create_app_kb():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='✅ Подтвердить', callback_data="accept_create_app")
    keyboard.button(text='❌ Отменить', callback_data="back_to_menu")
    keyboard.adjust(2)
    return keyboard.as_markup()


async def user_application_kb(objects, current_idx, current_page, method):
    keyboard = InlineKeyboardBuilder()
    for i in objects:
        keyboard.button(text=f'Заявка №{i.pk}', callback_data=ShowAppInfo(id=i.pk))
    keyboard.adjust(1)
    next_b = InlineKeyboardButton(text=">",
                                  callback_data=UserAppCallback(current_idx=current_idx + 5, method=method).pack())
    middle_b = InlineKeyboardButton(text=current_page,
                                    callback_data=UserAppCallback(current_idx=current_idx, method=method).pack())
    back_b = InlineKeyboardButton(text="<",
                                  callback_data=UserAppCallback(current_idx=current_idx - 5, method=method).pack())
    keyboard.row(back_b, middle_b, next_b)
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return keyboard.as_markup()


async def app_info_kb_kb(status, method, app_id):
    keyboard = InlineKeyboardBuilder()
    if status in ['open', 'in_work']:
        keyboard.button(text='Продолжить общение', callback_data=CompletedCommunication(id=app_id))
    else:
        keyboard.button(text='Вернуть на доработку', callback_data=BackInWork(id=app_id))
    keyboard.button(text='🔙 Назад', callback_data=UserAppCallback(current_idx=0, method=method))
    keyboard.adjust(1)
    return keyboard.as_markup()


async def feed_back_kb(app_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='1 ⭐️', callback_data=GradeCallback(grade=1, id=app_id))
    keyboard.button(text='2 ⭐️', callback_data=GradeCallback(grade=2, id=app_id))
    keyboard.button(text='3 ⭐️', callback_data=GradeCallback(grade=3, id=app_id))
    keyboard.button(text='4 ⭐️', callback_data=GradeCallback(grade=4, id=app_id))
    keyboard.button(text='5 ⭐️', callback_data=GradeCallback(grade=5, id=app_id))
    keyboard.button(text='Без оценки', callback_data=GradeCallback(grade=0, id=app_id))
    keyboard.button(text='Вернуть в работу', callback_data=BackInWork(id=app_id))
    return keyboard.adjust(5).as_markup()
