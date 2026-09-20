from django.contrib import admin

from .models import ModelVersion, TrainingJob


@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'dataset', 'status', 'epochs', 'accuracy', 'validation_accuracy',
        'created_by', 'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['dataset__name', 'task_id']
    readonly_fields = [f.name for f in TrainingJob._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = [
        'version', 'architecture', 'dataset', 'num_classes',
        'validation_accuracy', 'is_active', 'created_at',
    ]
    list_filter = ['is_active', 'architecture']
    search_fields = ['version', 'dataset__name']
    readonly_fields = [f.name for f in ModelVersion._meta.fields]

    def has_add_permission(self, request):
        return False
