"""Deadline/streak/inactivity eslatmalarini yuborish uchun periodik Celery task'lar."""
from celery import shared_task
from django.utils import timezone

from apps.notifications.models import Notification


@shared_task
def send_pending_notifications():
    """Har daqiqa chaqiriladi (beat schedule orqali). 'pending' va vaqti kelgan
    bildirishnomalarni Telegram API orqali yuboradi, flood-control'ga rioya qilib
    (masalan har chaqiriqda maksimal 25 tasini)."""
    import telebot
    from django.conf import settings

    bot = telebot.TeleBot(settings.BOT_TOKEN)
    due = Notification.objects.filter(status=Notification.PENDING, scheduled_for__lte=timezone.now())[:25]

    for n in due:
        try:
            bot.send_message(n.user.telegram_id, n.text)
            n.status = Notification.SENT
            n.sent_at = timezone.now()
        except Exception as e:  # noqa: BLE001
            n.status = Notification.FAILED
            n.error_message = str(e)[:255]
        n.save(update_fields=["status", "sent_at", "error_message"])


@shared_task
def enqueue_deadline_reminders():
    """Ertaga muddati tugaydigan tasklar uchun eslatma yaratadi (24 soat oldin)."""
    from apps.tasks.models import Task
    from services.notification_service import enqueue_notification

    window_start = timezone.now() + timezone.timedelta(hours=23)
    window_end = timezone.now() + timezone.timedelta(hours=25)
    tasks = Task.objects.filter(is_done=False, deadline__range=(window_start, window_end))

    for t in tasks:
        enqueue_notification(
            t.user, Notification.DEADLINE,
            f"⏰ Eslatma: '{t.title}' vazifasining muddati ertaga tugaydi!",
            scheduled_for=timezone.now(),
        )


@shared_task
def enqueue_inactivity_reminders():
    """3 kundan beri faol bo'lmagan userlarga eslatma (cooldown bilan — ortiqcha spam qilmaslik uchun)."""
    from apps.users.models import User
    from services.notification_service import enqueue_notification

    threshold = timezone.now() - timezone.timedelta(days=3)
    inactive_users = User.objects.filter(is_banned=False, last_active_at__lt=threshold)

    for u in inactive_users:
        enqueue_notification(
            u, Notification.INACTIVITY,
            "👋 Sog'inganingizni his qildik! Bugun bitta vazifa bajarib, streak'ingizni davom ettiring 🔥",
            scheduled_for=timezone.now(),
        )
