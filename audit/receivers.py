from django.dispatch import receiver
from accounts.signals import login_failed, user_logged_in_custom, user_logged_out_custom, user_registered
from .models import AuditLog
from .services import log_event


@receiver(user_registered)
def handle_user_registered(sender, user, request=None, **kwargs):
    log_event(
        AuditLog.EventType.USER_REGISTERED,
        user=user,
        request=request,
        description=f"New account registered for {user.email}.")


@receiver(user_logged_in_custom)
def handle_user_logged_in(sender, user, request=None, **kwargs):
    log_event(
        AuditLog.EventType.USER_LOGIN,
        user=user,
        request=request,
        description=f"{user.email} logged in.")


@receiver(user_logged_out_custom)
def handle_user_logged_out(sender, user, request=None, **kwargs):
    log_event(
        AuditLog.EventType.USER_LOGOUT,
        user=user,
        request=request,
        description=f"{user.email} logged out.")


@receiver(login_failed)
def handle_login_failed(sender, identifier, request=None, **kwargs):
    log_event(
        AuditLog.EventType.LOGIN_FAILED,
        user=None,
        request=request,
        actor_identifier=identifier,
        description=f"Failed login attempt for identifier '{identifier}'.")
