from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Audit Logging'

    def ready(self):
        # Connects receivers to accounts.signals (and, in later phases,
        # to imaging/training/classification signals). Importing here
        # ensures the connections are made exactly once, at app startup.
        import audit.receivers  # noqa: F401
