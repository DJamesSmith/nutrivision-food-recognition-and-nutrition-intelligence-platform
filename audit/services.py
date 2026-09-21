import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    if request is None:
        return None
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# Single write path for audit entries. Called either indirectly (via the signal receivers in audit.receivers, wired to accounts' auth signals)
# or directly by other apps (imaging/training/classification in later phases) for events that don't warrant a dedicated signal.
# Never pass passwords, JWT secrets, or other credential material in `metadata` or `description` — this function does not scrub input.
def log_event(event_type, user=None, request=None, description='', metadata=None, actor_identifier='', reference_model='', reference_id=''):
    try:
        AuditLog.objects.create(
            event_type=event_type,
            user=user if (user is not None and getattr(user, 'is_authenticated', True)) else None,
            actor_identifier=actor_identifier or (getattr(user, 'email', '') or ''),
            description=description,
            ip_address=get_client_ip(request),
            metadata=metadata or {},
            reference_model=reference_model,
            reference_id=str(reference_id) if reference_id else '')
    except Exception:
        # Audit logging must never break the primary request/task. Log the failure to the application logger instead of raising.
        logger.exception("Failed to write audit log entry for event_type=%s", event_type)