from datetime import date

from django import forms
from import_export import resources, fields
from import_export.forms import ExportForm
from import_export.widgets import ForeignKeyWidget, DateWidget

from admin_panel.telebot.models import Application, Client


class ExportFilterForm(ExportForm):
    date_from = forms.DateField(
        required=False,
        label='Дата от',
        widget=forms.SelectDateWidget(
            years=range(2022, date.today().year + 1)
        )
    )
    date_to = forms.DateField(
        required=False,
        label='Дата до',
        widget=forms.SelectDateWidget(
            years=range(2022, date.today().year + 1)
        )
    )
    company = forms.ChoiceField(
        choices=[("all", "Все")] + list(
            Client.objects.exclude(company__isnull=True).order_by('company').values_list('company',
                                                                                         'company').distinct()),
        required=False,
        label='Компания'
    )
    status = forms.ChoiceField(
        choices=[("all", "Все")] + list(Application.status_choice), required=False,
        label='Статус'
    )


class ApplicationResource(resources.ModelResource):
    id = fields.Field(attribute='id', column_name='ID')
    user = fields.Field(
        column_name='Пользователь',
        attribute='user',
        widget=ForeignKeyWidget(Client, field='fcs'))
    text = fields.Field(attribute='text', column_name='Текст')
    company = fields.Field(attribute='company', column_name='Компания')
    created = fields.Field(attribute='created', column_name='Дата создания',
                           widget=DateWidget(format='%d.%m.%Y %H:%M'))
    status = fields.Field(attribute='status', column_name='Статус')
    completed_time = fields.Field(attribute='completed_time', column_name='Выполнена',
                                  widget=DateWidget(format='%d.%m.%Y %H:%M'))
    grade = fields.Field(attribute='grade', column_name='Оценка')

    def dehydrate_status(self, app: Application):
        return app.get_status_display()

    def dehydrate_company(self, app: Application):
        return app.user.company

    class Meta:
        model = Application
        fields = ('id', 'user', 'company', 'text', 'status', 'created', 'completed_time', 'grade')
        export_order = ('id', 'user', 'company', 'text', 'status', 'created', 'completed_time', 'grade')
