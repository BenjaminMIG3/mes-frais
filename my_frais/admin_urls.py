"""
URLs pour l'interface admin des logs MongoDB
"""
from django.urls import path
from .admin_views import (
    logs_dashboard,
    logs_auth_events,
    logs_crud_events,
    logs_errors,
    logs_business_events,
    LogsAPIView
)

app_name = 'mongodb_logs'

urlpatterns = [
    path('', logs_dashboard, name='dashboard'),
    path('auth/', logs_auth_events, name='auth'),
    path('crud/', logs_crud_events, name='crud'),
    path('errors/', logs_errors, name='errors'),
    path('business/', logs_business_events, name='business'),
    path('api/<str:collection>/', LogsAPIView.as_view(), name='api'),
] 