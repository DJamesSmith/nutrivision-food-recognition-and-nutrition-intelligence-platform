from django.urls import path

from . import api_views, views

app_name = 'classification'

urlpatterns = [

    # ==================================================
    # TEMPLATE / WEB URLS
    # ==================================================

    path('predict/', views.predict_view, name='predict'),
    path('history/', views.history_view, name='history'),

    # ==================================================
    # REST API URLS
    # ==================================================

    path('api/classification/predict/', api_views.predict_api, name='api_predict'),
    path('api/classification/history/', api_views.history_api, name='api_history'),
]
