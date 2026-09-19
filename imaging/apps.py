from django.apps import AppConfig


class ImagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'imaging'
    verbose_name = 'Image & Dataset Management'

    def ready(self):
        # Registers pre_save/post_delete receivers for automatic image lifecycle handling (old-file cleanup, on-delete cleanup).
        import imaging.signals  # noqa: F401
