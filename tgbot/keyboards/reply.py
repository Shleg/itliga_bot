from aiogram.utils.keyboard import ReplyKeyboardBuilder


async def close_support_chat_kb():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text='Завершить диалог')
    return keyboard.adjust(1).as_markup(resize_keyboard=True, one_time_keyboard=True)
