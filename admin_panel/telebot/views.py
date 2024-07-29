from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from dotenv import load_dotenv

from admin_panel.telebot.models import Application, Operators, Settings

load_dotenv()


@login_required
def export_conversation(request, application_id):
    template = 'tgbot/chat.html'
    application = Application.objects.get(id=application_id)
    messages_list = application.messages.all()
    status_dict = {
        'open': 'Открыта',
        'in_work': 'В работе',
        'done': 'Выполнено',
        'closed': 'Закрыто',
    }
    return render(request, template, {
        'messages_list': messages_list,
        'application_id': application_id,
        'status': status_dict[application.status],
    })


@login_required
def operator_stats(request, operator_id):
    template = 'tgbot/operator_stats.html'
    operator = get_object_or_404(Operators, id=operator_id)

    now = datetime.now()
    a_week_ago = now - timedelta(weeks=1)
    a_month_ago = now - timedelta(weeks=4)
    a_year_ago = now - timedelta(days=365)

    closed_applications = operator.applications.filter(status='closed')

    week_stats = closed_applications.filter(completed_time__gte=a_week_ago).count()
    month_stats = closed_applications.filter(completed_time__gte=a_month_ago).count()
    year_stats = closed_applications.filter(completed_time__gte=a_year_ago).count()

    context = {
        'operator': operator,
        'week_stats': week_stats,
        'month_stats': month_stats,
        'year_stats': year_stats,
    }

    return render(request, template, context)


@login_required
def settings(request):
    template = 'tgbot/setting.html'
    if request.method == 'POST':
        Settings.objects.filter(name_setting='not_online_message').update(value=request.POST['not_available'])
        context = {
            'not_online_message': request.POST['not_available'],
            'saved': True,
        }
        return render(request, template, context)
    not_online_message = Settings.objects.get(name_setting="not_online_message").value
    context = {
        'not_online_message': not_online_message,
    }
    return render(request, template, context)
