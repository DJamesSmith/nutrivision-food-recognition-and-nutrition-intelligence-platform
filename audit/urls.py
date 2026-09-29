from django.urls import path
from .views import api_views
from .views import views

app_name = 'audit'

urlpatterns = [
    path('audit/', views.audit_log_view, name='audit_log_list'),                                        # TEMPLATE / WEB URLS
    path('api/audit/logs/', api_views.audit_log_list_api, name='api_audit_log_list'),                   # REST API URLS
]
