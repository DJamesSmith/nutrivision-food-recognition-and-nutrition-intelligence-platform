from django.urls import path

from . import api_views, views

app_name = 'imaging'

urlpatterns = [

    # ==================================================
    # TEMPLATE / WEB URLS
    # ==================================================

    path('datasets/', views.dataset_list_view, name='dataset_list'),
    path('datasets/create/', views.dataset_create_view, name='dataset_create'),
    path('datasets/<int:dataset_id>/', views.dataset_detail_view, name='dataset_detail'),

    # ==================================================
    # REST API URLS
    # ==================================================

    path('api/imaging/datasets/', api_views.dataset_list_create_api, name='api_dataset_list_create'),
    path('api/imaging/datasets/<int:dataset_id>/', api_views.dataset_detail_api, name='api_dataset_detail'),
    path(
        'api/imaging/datasets/<int:dataset_id>/images/',
        api_views.dataset_image_upload_api,
        name='api_dataset_image_upload',
    ),
    path(
        'api/imaging/datasets/<int:dataset_id>/images/<int:image_id>/',
        api_views.dataset_image_delete_api,
        name='api_dataset_image_delete',
    ),
    path('api/imaging/images/upload/', api_views.uploaded_image_create_api, name='api_uploaded_image_create'),
]
