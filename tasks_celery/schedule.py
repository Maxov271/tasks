"""
Celery beat jadvali. config/settings/base.py ichidagi CELERY_BEAT_SCHEDULE
shu yerdan import qilinadi (yoki to'g'ridan-to'g'ri shu faylni import qilib ulanadi).
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "send-pending-notifications-every-minute": {
        "task": "tasks_celery.reminders.send_pending_notifications",
        "schedule": 60.0,
    },
    "enqueue-deadline-reminders-hourly": {
        "task": "tasks_celery.reminders.enqueue_deadline_reminders",
        "schedule": crontab(minute=0),
    },
    "enqueue-inactivity-reminders-daily": {
        "task": "tasks_celery.reminders.enqueue_inactivity_reminders",
        "schedule": crontab(hour=10, minute=0),
    },
    "daily-backup": {
        "task": "tasks_celery.backups.run_daily_backup",
        "schedule": crontab(hour=3, minute=0),
    },
    "daily-stats-snapshot": {
        "task": "tasks_celery.stats_snapshot.generate_bot_daily_snapshot",
        "schedule": crontab(hour=0, minute=5),
    },
}
