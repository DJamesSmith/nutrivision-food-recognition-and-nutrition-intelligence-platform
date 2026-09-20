from django.urls import path

from . import api_views, views

app_name = 'training'

urlpatterns = [

    # ==================================================
    # TEMPLATE / WEB URLS
    # ==================================================

    path('training/', views.training_dashboard_view, name='training_dashboard'),
    path('training/jobs/<int:job_id>/', views.training_job_detail_view, name='training_job_detail'),

    # ==================================================
    # REST API URLS
    # ==================================================

    path('api/training/train/', api_views.train_api, name='api_train'),
    path('api/training/jobs/', api_views.training_job_list_api, name='api_training_job_list'),
    path('api/training/jobs/<int:job_id>/', api_views.training_job_detail_api, name='api_training_job_detail'),
    path('api/training/models/', api_views.model_version_list_api, name='api_model_version_list'),
    path(
        'api/training/models/<int:version_id>/activate/',
        api_views.model_version_activate_api,
        name='api_model_version_activate',
    ),
]
