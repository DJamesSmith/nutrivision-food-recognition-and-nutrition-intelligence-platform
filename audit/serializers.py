from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'event_type', 'user_email', 'actor_identifier', 'description',
            'ip_address', 'metadata', 'reference_model', 'reference_id', 'created_at',
        ]
        read_only_fields = fields
