import asyncio

from django.db import models
from django.db.models.signals import post_save, post_init

from admin_panel.telebot.close_topic import close_thread


class CreatedModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения"
    )

    class Meta:
        abstract = True


class Client(CreatedModel):
    username = models.CharField(
        max_length=50,
        help_text='Username клиента',
        verbose_name='Username',
        blank=True,
        null=True
    )
    telegram_id = models.BigIntegerField(
        help_text='Telegram ID пользователя',
        verbose_name='Telegram ID'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Имя в Telegram',
        help_text='Имя в Telegram'
    )
    url = models.CharField(
        max_length=255,
        verbose_name='Ссылка на пользователя'
    )
    fcs = models.CharField(
        verbose_name='ФИО клиента',
        max_length=150,
        blank=True,
        null=True
    )
    company = models.CharField(
        verbose_name='Название компании клиента',
        max_length=200,
        blank=True,
        null=True
    )
    is_blocked = models.BooleanField(
        verbose_name='Блокировка пользователя',
        default=False
    )
    export = models.BooleanField(
        default=False,
        verbose_name='Разрешить/Запретить экспорт'
    )

    class Meta:
        verbose_name = 'Клиенты телеграмм бота'
        verbose_name_plural = 'Клиенты телеграмм бота'
        ordering = ('-created',)

    def __str__(self):
        return "{} ({})".format(self.username, self.telegram_id)


class Operators(CreatedModel):
    username = models.CharField(
        max_length=50,
        help_text='Username клиента',
        verbose_name='Username',
        blank=True,
        null=True
    )
    telegram_id = models.BigIntegerField(
        help_text='Telegram ID пользователя',
        verbose_name='Telegram ID'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Имя в Telegram',
        help_text='Имя в Telegram'
    )
    url = models.CharField(
        max_length=255,
    )

    class Meta:
        verbose_name = 'Операторы'
        verbose_name_plural = 'Операторы'
        ordering = ('-created',)

    def __str__(self):
        return self.name


class Application(CreatedModel):
    status_choice = (
        ('open', 'Открыта'),
        ('in_work', 'В работе'),
        ('done', 'Выполнено'),
        ('closed', 'Закрыто'),
    )
    user = models.ForeignKey(
        Client,
        verbose_name='Пользователь',
        related_name='applications',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    text = models.TextField(
        verbose_name='Содержание'
    )
    message_thread_id = models.BigIntegerField(
        blank=True,
        null=True
    )
    completed_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Время закрытия'
    )
    status = models.CharField(
        verbose_name='Статус',
        max_length=50,
        choices=status_choice,
        default='open'
    )
    grade = models.IntegerField(
        verbose_name='Оценка от пользователя',
        blank=True,
        null=True,
    )
    operator = models.ForeignKey(
        Operators,
        blank=True,
        null=True,
        verbose_name='Оператор',
        related_name='applications',
        on_delete=models.SET_NULL
    )

    @staticmethod
    def post_save(sender, instance, created, **kwargs):
        if instance.previous_state != instance.status and instance.status == 'closed':
            if instance.message_thread_id:
                Application.objects.filter(pk=instance.pk).update(message_thread_id=None)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(close_thread(instance.message_thread_id))

    @staticmethod
    def remember_state(sender, instance, **kwargs):
        instance.previous_state = instance.status

    class Meta:
        verbose_name = 'Заявки'
        verbose_name_plural = 'Заявки'
        ordering = ('-created',)

    def __str__(self):
        return self.text[:100]


class Message(models.Model):
    sender_choice = (
        ('user', 'Пользователь'),
        ('admin', 'Оператор'),
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    text = models.TextField(
        blank=True,
        null=True
    )
    image = models.ImageField(upload_to='image/', blank=True)
    file = models.FileField(upload_to='file/', blank=True)
    date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(
        verbose_name='Имя собеседника',
        max_length=250
    )
    sender = models.CharField(
        verbose_name='Отправитель',
        max_length=50,
        default='user',
        choices=sender_choice
    )
    message_type = models.CharField(max_length=20, choices=[
        ('text', 'Текст'),
        ('image', 'Изображение'),
        ('file', 'Файл')
    ])

    class Meta:
        ordering = ['date']


class Settings(models.Model):
    name_setting = models.CharField(max_length=255)
    value = models.CharField(max_length=4096)

    def __str__(self):
        return self.name_setting


post_save.connect(Application.post_save, sender=Application)
post_init.connect(Application.remember_state, sender=Application)
