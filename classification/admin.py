from django.contrib import admin

from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'predicted_class', 'confidence', 'model_version', 'created_at']
    list_filter = ['model_version', 'created_at']
    search_fields = ['predicted_class', 'user__email']
    readonly_fields = [f.name for f in Prediction._meta.fields]

    def has_add_permission(self, request):
        # Predictions are only ever created through the inference pipeline.
        return False
