import math
from datetime import datetime
from io import BytesIO
from typing import Union, Optional

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, InputFile, InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove, ForceReply
from aiogram.utils.markdown import hitalic
from django.core.files.base import ContentFile
from pydantic import ValidationError

from tgbot.models.db_commands import create_messages


async def one_message_editor(
        event: CallbackQuery | Message,
        text: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]] = None,
        photo: Union[InputFile, str] = None,
        document: Union[InputFile, str] = None,
        video: Union[InputFile, str] = None,
        parse_mode: Optional[str] = 'HTML',
        disable_web_page_preview: bool = False,
):
    """
        Этот метод служит для автоматического изменения/удаления предыдущего сообщения для того чтобы не захламлять
        чат и был вид одного сообщения. Можно отправлять Текст, Фото, Видео, Документы.

        :param event: Объект, который принимает handler, может быть CallbackQuery или Message
        :param text: Текст сообщения либо описание под медиа
        :param reply_markup: Клавиатура отправляемая с сообщением
        :param photo: Передавайте если хотите отправить фото
        :param document: Передавайте если хотите отправить документ
        :param video: Передавайте если хотите отправить видео
        :param parse_mode: Передавайте если хотите изменить parse_mode. Default = HTML
        :param disable_web_page_preview: Показывать преью сайта в сообщении или нет. Default = False
    """
    content_type = [ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT]

    if isinstance(event, CallbackQuery) and not photo and not video and not document \
            and not event.message.content_type in content_type:
        try:
            await event.message.edit_text(text=text, parse_mode=parse_mode, reply_markup=reply_markup,
                                          disable_web_page_preview=disable_web_page_preview)
        except TelegramBadRequest:
            try:
                await event.message.delete()
            except TelegramBadRequest:
                pass
            await event.message.answer(text=text, parse_mode=parse_mode, reply_markup=reply_markup,
                                       disable_web_page_preview=disable_web_page_preview)
        except ValidationError:
            try:
                await event.message.delete()
            except TelegramBadRequest:
                pass
            await event.message.answer(text=text, parse_mode=parse_mode, reply_markup=reply_markup,
                                       disable_web_page_preview=disable_web_page_preview)
    else:
        if isinstance(event, CallbackQuery):
            event = event.message
        try:
            await event.delete()
        except TelegramBadRequest:
            pass
        if photo:
            await event.answer_photo(photo=photo, caption=text, reply_markup=reply_markup, parse_mode=parse_mode,
                                     disable_web_page_preview=disable_web_page_preview)
        elif video:
            await event.answer_video(video=video, caption=text, reply_markup=reply_markup, parse_mode=parse_mode,
                                     disable_web_page_preview=disable_web_page_preview)
        elif document:
            await event.answer_document(document=document, caption=text, reply_markup=reply_markup,
                                        parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview)
        else:
            await event.answer(text=text, reply_markup=reply_markup, parse_mode=parse_mode,
                               disable_web_page_preview=disable_web_page_preview)


async def support_chat(bot: Bot, message: Message, chat_id: int,
                       message_thread_id: int = None, app_id: int = None, app_text: str = None) -> None:
    """
        Отправляет сообщение от пользователя в поддержку чата, и отправляет ответ обратно.

        :param bot: Объект бота
        :param message: Объект сообщения от пользователя или техх поддержки
        :param chat_id: чат в который хотим отправить сообщение
        :param message_thread_id: если сообщение от пользователя то указываем id темы
        :return: None
    """
    send_methods = {
        "photo": bot.send_photo,
        "video": bot.send_video,
        "document": bot.send_document,
        "voice": bot.send_voice,
        "audio": bot.send_audio,
        "sticker": bot.send_sticker,
        "animation": bot.send_animation,
        "contact": bot.send_contact,
        "venue": bot.send_venue,
        "location": bot.send_location,
        "video_note": bot.send_video_note,
        "poll": bot.send_poll
    }

    send_method = send_methods.get(message.content_type)
    if send_method:
        args = [chat_id]
        kwargs = {"message_thread_id": message_thread_id}

        if message.content_type in ["photo", "video", "document", "voice", "audio", "animation", "video_note",
                                    "sticker"]:
            if message.content_type == "photo":
                args.append(getattr(message, message.content_type)[-1].file_id)
            else:
                args.append(getattr(message, message.content_type).file_id)
            if message.caption:
                kwargs["caption"] = message.caption
        elif message.content_type == "contact":
            contact = message.contact
            kwargs.update({
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "phone_number": contact.phone_number,
                "vcard": contact.vcard
            })
        elif message.content_type == "venue":
            venue = message.venue
            kwargs.update({
                "latitude": venue.location.latitude,
                "longitude": venue.location.longitude,
                "address": venue.address,
                "title": venue.title,
                "foursquare_id": venue.foursquare_id,
                "foursquare_type": venue.foursquare_type,
                "google_place_type": venue.google_place_type,
                "google_place_id": venue.google_place_id
            })
        elif message.content_type == "location":
            location = message.location
            kwargs.update({
                "latitude": location.latitude,
                "longitude": location.longitude,
                "horizontal_accuracy": location.horizontal_accuracy,
                "proximity_alert_radius": location.proximity_alert_radius,
                "heading": location.heading
            })
        elif message.content_type == "poll":
            pool = message.poll
            kwargs.update({
                "options": [i.text for i in pool.options],
                "allows_multiple_answers": pool.allows_multiple_answers,
                "question": pool.question,
                "type": pool.type,
                "is_anonymous": pool.is_anonymous,
                "is_closed": pool.is_closed,
                "correct_option_id": 0,
                "explanation": pool.explanation,
                "explanation_entities": pool.explanation_entities,
                "open_period": pool.open_period,
            })

        await send_method(*args, **kwargs)
    else:
        if app_id and app_text:
            text = [
                hitalic(f"[Оператор: {message.from_user.full_name}]"),
                hitalic(f"[Заявка №{app_id} {app_text[:10]}]"),
                message.text
            ]
            text = '\n'.join(text)
        else:
            text = message.text
        await bot.send_message(chat_id=chat_id, text=text,
                               reply_to_message_id=message_thread_id)


async def create_message_history(message: Message, sender, app, bot, author):
    if message.photo:
        photo_info = await bot.get_file(message.photo[-1].file_id)
        photo = BytesIO()
        message_history = await create_messages(sender, author, app, 'image')
        await bot.download_file(photo_info.file_path, destination=photo)
        photo_file = ContentFile(photo.getvalue())
        message_history.image.save(name=photo_info.file_path.split('/')[1], content=photo_file, save=True)
    elif message.document:
        doc_info = await bot.get_file(message.document.file_id)
        doc = BytesIO()
        message_history = await create_messages(sender, author, app, 'file')
        await bot.download_file(doc_info.file_path, destination=doc)
        doc_file = ContentFile(doc.getvalue())
        message_history.file.save(name=doc_info.file_path.split('/')[1], content=doc_file, save=True)
    elif message.text:
        await create_messages(sender, author, app, 'text', message.text)
    elif message.video:
        await create_messages(sender, author, app, 'text', '🏷 Отправил видео')
    elif message.animation:
        await create_messages(sender, author, app, 'text', '🏷 Отправил gif')
    elif message.audio:
        await create_messages(sender, author, app, 'text', '🏷 Отправил аудио')
    elif message.sticker:
        await create_messages(sender, author, app, 'text', '🏷 Отправил стикер')
    elif message.contact:
        await create_messages(sender, author, app, 'text', '🏷 Отправил контакт')
    elif message.location:
        await create_messages(sender, author, app, 'text', '🏷 Отправил локацию')
    elif message.video_note:
        await create_messages(sender, author, app, 'text', '🏷 Отправил видео-кружок')
    elif message.venue:
        await create_messages(sender, author, app, 'text', '🏷 Отправил место встречи')
    elif message.poll:
        await create_messages(sender, author, app, 'text', '🏷 Отправил опрос')
    elif message.voice:
        await create_messages(sender, author, app, 'text', '🏷 Отправил голосовое сообщение')


async def pagination(elements, current_index, page_size):
    # Определяем границы среза
    start_index = current_index
    end_index = current_index + page_size

    # Корректируем границы среза, если они выходят за пределы списка
    if start_index <= 0:
        current_index = 0
        start_index = 0
        end_index = page_size
    elif start_index >= len(elements):  # Если ушли за пределы списка вправо
        end_index = current_index
        start_index = current_index - page_size
        current_index = start_index

    current_page = current_index // page_size + 1  # Получаем текущую страницу
    count_page = math.ceil(len(elements) / page_size)  # Получаем последнюю страницу
    return elements[start_index:end_index], current_index, f"{current_page}/{count_page}"


async def check_time_status():
    now = datetime.now()

    if 0 <= now.weekday() <= 4:
        if 9 <= now.hour < 19:
            return True
        else:
            return False
    else:
        return False
