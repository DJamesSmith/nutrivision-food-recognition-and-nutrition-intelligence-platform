from django.contrib import admin

from .models import Dataset, DatasetImage, UploadedImage


class DatasetImageInline(admin.TabularInline):
    model = DatasetImage
    extra = 0
    readonly_fields = ['image', 'class_label', 'uploaded_by', 'created_at']
    can_delete = True


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'get_num_images', 'get_num_classes', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name']
    inlines = [DatasetImageInline]

    @admin.display(description='Images')
    def get_num_images(self, obj):
        return obj.get_num_images()

    @admin.display(description='Classes')
    def get_num_classes(self, obj):
        return obj.get_num_classes()


@admin.register(DatasetImage)
class DatasetImageAdmin(admin.ModelAdmin):
    list_display = ['dataset', 'class_label', 'uploaded_by', 'created_at']
    list_filter = ['dataset', 'class_label']
    search_fields = ['class_label', 'dataset__name']


@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ['user', 'original_filename', 'file_size', 'created_at']
    search_fields = ['user__email', 'original_filename']
    readonly_fields = ['content_type', 'file_size', 'created_at']
