"""Celery ilova instansi. Ishga tushirish: celery -A tasks_celery.celery_app worker -B -l info"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("telegram_workspace")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["tasks_celery"])
