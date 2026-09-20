from django.db import transaction

from .models import ModelVersion


def get_active_model_version():
    """
    The single lookup point for 'which model should be used for
    prediction right now'. The classification app (Phase 5) calls this
    instead of hard-coding any model path.
    """
    return ModelVersion.objects.filter(is_active=True).order_by('-created_at').first()


def activate_model_version(model_version):
    """
    Marks `model_version` as the active one and deactivates every other
    version, atomically. There is at most one active ModelVersion at any
    time.
    """
    with transaction.atomic():
        ModelVersion.objects.exclude(pk=model_version.pk).filter(is_active=True).update(is_active=False)
        if not model_version.is_active:
            model_version.is_active = True
            model_version.save(update_fields=['is_active'])
