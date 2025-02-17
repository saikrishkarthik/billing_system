import os
from celery import Celery

os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")  # Prevents multiprocessing issue on Windows

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing_system.settings")

app = Celery("billing_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
