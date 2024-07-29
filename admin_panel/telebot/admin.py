from datetime import date

from django.contrib import admin
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin

from admin_panel.telebot.models import Application, Client, Operators
from admin_panel.telebot.resources import ApplicationResource, ExportFilterForm


class BotAdminSite(AdminSite):
    site_title = "Управление ботом"
    site_header = "Управление ботом"
    index_title = ""

    def get_app_list(self, request, *args):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request)
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])
        new_models = [
            {
                "name": "Настройки",
                "add_url": reverse(f'panel:settings'),
                "admin_url": reverse(f'panel:settings'),
                "view_only": True
            },
        ]
        for app in app_list:
            if app['app_label'] == 'telebot':
                app['models'].extend(new_models)

        return app_list


bot_admin = BotAdminSite()


@admin.register(User, site=bot_admin)
class UserAdmin(ModelAdmin):
    list_display = (
        'pk',
        'first_name',
        'last_name',
        'username',
        'email',
    )

    fields = (
        'first_name', 'last_name', 'username', 'password', 'email')

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.set_password(obj.password)
        obj.save()
        super().save_model(request, obj, form, change)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    class Meta:
        verbose_name_plural = 'Менеджеры'


# @admin.register(Group, site=bot_admin)
# class GroupAdmin(ModelAdmin):
#     list_display = (
#         'name',
#         'objects',
#     )
#
#     class Meta:
#         verbose_name_plural = 'Группы'
#

@admin.register(Client, site=bot_admin)
class ClientAdmin(ModelAdmin):
    list_display = (
        'pk',
        'name',
        'user_link',
        'username',
        'telegram_id',
        'fcs',
        'company',
        'is_blocked',
        'export'
    )
    list_display_links = ('pk', 'username')
    empty_value_display = '-пусто-'
    list_editable = ('fcs', 'company', 'is_blocked', 'export')

    def user_link(self, object: Client):
        if object.username and object.name:
            return format_html('<a href="https://t.me/{}">{}</a>', object.username, object.name)
        else:
            return object.url

    user_link.short_description = "Ссылка"

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_staff

    class Meta:
        verbose_name_plural = 'Клиенты бота'


@admin.register(Application, site=bot_admin)
class ApplicationAdmin(ImportExportModelAdmin):
    resource_class = ApplicationResource
    list_display = ('pk', 'user', 'text', 'company_mode', 'messages_mod', 'status', 'operator')
    list_display_links = ('pk',)
    list_editable = ('status', 'text')
    list_filter = ('status', 'user', 'created', 'user__company',)
    search_fields = ('pk',)

    def messages_mod(self, object):
        href = reverse('panel:conversation', kwargs={'application_id': object.id})
        return mark_safe(f"<a href='{href}'>Перейти к переписке</a>")

    messages_mod.short_description = 'Переписка'

    def company_mode(self, object: Application):
        if object.user:
            return object.user.company
        else:
            return ''

    company_mode.short_description = 'Компания'

    def get_export_form_class(self):
        return ExportFilterForm

    def get_export_queryset(self, request):
        queryset = super().get_export_queryset(request)

        date_from = None
        date_to = None
        company = request.POST.get('company')
        status = request.POST.get('status')

        if request.POST.get('date_from_day') and request.POST.get('date_from_month') and request.POST.get(
                'date_from_year'):
            date_from = date(
                year=int(request.POST.get('date_from_year')),
                month=int(request.POST.get('date_from_month')), day=int(request.POST.get('date_from_day')))

        if request.POST.get('date_to_day') and request.POST.get('date_to_month') and request.POST.get(
                'date_to_year'):
            date_to = date(
                year=int(request.POST.get('date_to_year')),
                month=int(request.POST.get('date_to_month')), day=int(request.POST.get('date_to_day')))

        if date_from:
            queryset = queryset.filter(created__gte=date_from)
        if date_to:
            queryset = queryset.filter(created__lte=date_to)
        if company and company != "all":
            queryset = queryset.filter(user__company=company)
        if status and status != "all":
            queryset = queryset.filter(status=status)

        return queryset

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_staff

    class Meta:
        verbose_name_plural = 'Медиа заявки'


@admin.register(Operators, site=bot_admin)
class OperatorsAdmin(ModelAdmin):
    list_display = (
        'username',
        'telegram_id',
        'name',
        'count_close_app',
        'view_stats_link'
    )
    list_display_links = ('username',)

    def count_close_app(self, object: Operators):
        return object.applications.all().count()

    def view_stats_link(self, obj):
        url = reverse('panel:operator_stats', args=[obj.pk])
        return format_html('<a href="{}">Открыть статистику</a>', url)

    view_stats_link.short_description = 'Статистика'

    count_close_app.short_description = "Закрытые заявки"

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_staff

    class Meta:
        verbose_name_plural = 'Операторы'
