"""Og'ir statistik agregatsiyalarni oldindan hisoblab, StatsSnapshot jadvaliga yozadi."""
from celery import shared_task
from django.utils import timezone

from apps.users.models import User
from apps.tasks.models import Task
from apps.groups.models import Group
from apps.statistics.models import StatsSnapshot


@shared_task
def generate_bot_daily_snapshot():
    today = timezone.localdate()
    data = {
        "total_users": User.objects.count(),
        "new_today": User.objects.filter(created_at__date=today).count(),
        "active_today": User.objects.filter(last_active_at__date=today).count(),
        "tasks_done_today": Task.objects.filter(done_at__date=today).count(),
        "total_groups": Group.objects.filter(is_active=True).count(),
    }
    StatsSnapshot.objects.create(scope=StatsSnapshot.BOT, period="daily", data=data)
