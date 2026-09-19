from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'event_type', 'actor_identifier', 'user', 'ip_address', 'description']
    list_filter = ['event_type', 'created_at']
    search_fields = ['actor_identifier', 'description', 'user__email']
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    ordering = ['-created_at']

    def has_add_permission(self, request):
        # Audit logs are only ever created programmatically.
        return False

    def has_change_permission(self, request, obj=None):
        return False
