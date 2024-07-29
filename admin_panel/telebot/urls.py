from django.urls import path

from . import views

app_name = 'panel'

urlpatterns = [
    path('conversation/<int:application_id>/', views.export_conversation, name='conversation'),
    path('operator/<int:operator_id>/stats/', views.operator_stats, name='operator_stats'),
    path('setting', views.settings, name='settings'),
]
