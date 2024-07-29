from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.config import Config


class AdminFilter(BaseFilter):
    is_admin: bool = True

    async def __call__(self, obj: Message, config: Config) -> bool:
        return (obj.from_user.id in config.tg_bot.admin_ids) == self.is_admin


class AnswerSupportFilter(BaseFilter):
    async def __call__(self, obj: Message, config: Config) -> bool:
        content_types = await get_content_types()
        if obj.reply_to_message and obj.content_type in content_types:
            return obj.chat.type == "supergroup" and obj.chat.id == config.misc.chat_support


async def get_content_types():
    return [ContentType.PHOTO, ContentType.VIDEO, ContentType.TEXT, ContentType.ANIMATION,
            ContentType.DOCUMENT,
            ContentType.VOICE, ContentType.AUDIO, ContentType.STICKER, ContentType.CONTACT,
            ContentType.LOCATION,
            ContentType.VIDEO_NOTE, ContentType.VENUE, ContentType.POLL]
