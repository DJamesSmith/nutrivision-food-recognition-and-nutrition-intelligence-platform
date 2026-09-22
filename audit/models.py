from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class EventType(models.TextChoices):
        USER_REGISTERED = 'USER_REGISTERED', 'User Registered'
        USER_LOGIN = 'USER_LOGIN', 'User Login'
        USER_LOGOUT = 'USER_LOGOUT', 'User Logout'
        LOGIN_FAILED = 'LOGIN_FAILED', 'Login Failed'
        IMAGE_UPLOADED = 'IMAGE_UPLOADED', 'Image Uploaded'
        PREDICTION_CREATED = 'PREDICTION_CREATED', 'Prediction Created'
        TRAINING_STARTED = 'TRAINING_STARTED', 'Training Started'
        TRAINING_COMPLETED = 'TRAINING_COMPLETED', 'Training Completed'
        TRAINING_FAILED = 'TRAINING_FAILED', 'Training Failed'
        MODEL_UPDATED = 'MODEL_UPDATED', 'Model Updated'

    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)

    # Nullable + SET_NULL: a deleted user's audit trail must survive the user's deletion (compliance/forensics), so we never cascade-delete logs.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')                     # ForeignKey
    # Preserves a human-readable identifier even after the user is gone.
    actor_identifier = models.CharField(max_length=254, blank=True)

    description = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Free-form, non-sensitive contextual data (e.g. {"model_version": "v3"}). Never store passwords, tokens, or other credential material here.
    metadata = models.JSONField(default=dict, blank=True)

    # Loose reference to whatever object the event concerns (a prediction id, a training job id, ...) without requiring a hard FK/contenttypes
    # dependency across apps that may not exist yet in earlier phases.
    reference_model = models.CharField(max_length=100, blank=True)
    reference_id = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        who = self.actor_identifier or (self.user_id and f"user #{self.user_id}") or "anonymous"
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.event_type} — {who}"
