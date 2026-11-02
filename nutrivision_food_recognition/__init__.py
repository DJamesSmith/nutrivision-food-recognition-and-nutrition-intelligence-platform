# Loads the Celery app whenever Django starts, so @shared_task (training/tasks.py) binds to THIS app and its CELERY_* settings, not
# Celery's bare default app.
from .celery import app as celery_app

__all__ = ('celery_app',)
