from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Accounts & Authentication'

    # Ensures signal senders in accounts.signals are importable/registered as soon as the app loads.
    # Receivers (e.g. the Phase 2 audit app) connect to these signals independently.
    def ready(self):
        import accounts.signals  # noqa: F401
