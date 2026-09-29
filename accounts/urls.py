from django.urls import path
from .views import api_views
from .views import views

app_name = 'accounts'

urlpatterns = [
    # TEMPLATE / WEB URLS (session authentication)
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # REST API URLS (JWT authentication)
    path('api/accounts/register/', api_views.register_api, name='api_register'),
    path('api/accounts/login/', api_views.login_api, name='api_login'),
    path('api/accounts/refresh/', api_views.refresh_api, name='api_refresh'),
    path('api/accounts/logout/', api_views.logout_api, name='api_logout'),
    path('api/accounts/me/', api_views.me_api, name='api_me'),
]
