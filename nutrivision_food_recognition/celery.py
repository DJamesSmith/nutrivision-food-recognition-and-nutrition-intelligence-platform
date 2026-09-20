import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrivision_food_recognition.settings')
app = Celery('nutrivision_food_recognition')

# Reads every CELERY_* key from Django settings.py (namespace='CELERY' strips the prefix, so CELERY_BROKER_URL -> broker_url, etc.).
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discovers tasks.py inside every app listed in INSTALLED_APPS — this is why training/tasks.py needs no manual registration anywhere.
app.autodiscover_tasks()


# Simple connectivity check: run via `celery -A nutrivision_food_recognition call nutrivision_food_recognition.celery.debug_task`.
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
