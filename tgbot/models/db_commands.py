from datetime import timedelta

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from admin_panel.telebot.models import Client, Application, Message, Operators, Settings


@sync_to_async()
def select_client(telegram_id):
    """
    Возвращает пользователя по телеграм ID
    """
    return Client.objects.filter(telegram_id=telegram_id).first()


@sync_to_async()
def create_client(username, telegram_id, url, name):
    """
    Создает пользователя
    """
    Client.objects.create(telegram_id=telegram_id, username=username, url=url, name=name)


@sync_to_async()
def create_super_user(username, password):
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, password=password)


@sync_to_async()
def get_app_by_thread_id(thread_id):
    return Application.objects.filter(message_thread_id=thread_id).first()


@sync_to_async()
def create_app(user, text):
    return Application.objects.create(user=user, text=text)


@sync_to_async()
def get_app(app_id):
    return Application.objects.get(pk=app_id)


@sync_to_async()
def create_messages(sender, author, application, message_type, text=None):
    return Message.objects.create(sender=sender, author=author, application=application, message_type=message_type,
                                  text=text)


@sync_to_async()
def get_closed_app():
    now = timezone.now()
    day_ago = now - timedelta(days=1)
    return Application.objects.filter(completed_time__lte=day_ago, status='done')


@sync_to_async()
def get_operator(telegram_id, username, name, url):
    obj, created = Operators.objects.get_or_create(telegram_id=telegram_id,
                                                   defaults={
                                                       'username': username,
                                                       'name': name,
                                                       'url': url,
                                                   })
    return obj


@sync_to_async()
def set_default_setting():
    setting = Settings.objects.filter(name_setting="not_online_message").first()
    if not setting:
        Settings.objects.create(name_setting="not_online_message", value="Ваше обращение принято, зафиксировано, "
                                                                         "сохранено и будет взято в работу когда "
                                                                         "встанет солнце")


@sync_to_async()
def get_not_online_message():
    return Settings.objects.get(name_setting="not_online_message").value


@sync_to_async()
def get_application_by_company(company):
    return Application.objects.filter(user__company=company)
