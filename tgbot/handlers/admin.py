from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.markdown import hcode

from tgbot.filters.admin import AdminFilter

admin_router = Router()
admin_router.message.filter(AdminFilter())


@admin_router.message(F.content_type.in_(['photo', 'video', 'document']))
async def get_file_id(message: Message):
    if message.photo:
        file_id = message.photo[-1].file_id
        return await message.answer(f'File ID Фото: {hcode(file_id)}')
    elif message.video:
        file_id = message.video.file_id
        return await message.answer(f'File ID Видео: {hcode(file_id)}')
    elif message.document:
        file_id = message.document.file_id
        return await message.answer(f'File ID Документа: {hcode(file_id)}')
