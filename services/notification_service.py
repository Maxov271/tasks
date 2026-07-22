"""
Bildirishnomalarni navbatga qo'yish uchun servis. Haqiqiy yuborish
tasks_celery/reminders.py ichidagi Celery worker orqali amalga oshadi —
bu yerda faqat DB'ga yozish (enqueue) logikasi bor.
"""
from apps.notifications.models import Notification, NotificationPreference

# Har bir notification turi qaysi preference maydoniga mos kelishini bog'lash
TYPE_TO_PREF_FIELD = {
    Notification.DEADLINE: "deadline_reminders",
    Notification.HOMEWORK: "homework_reminders",
    Notification.INACTIVITY: "inactivity_reminders",
    Notification.STREAK: "streak_reminders",
    Notification.ANNOUNCEMENT: "announcements",
}


def enqueue_notification(user, notification_type: str, text: str, scheduled_for):
    """Foydalanuvchining shu turdagi bildirishnomani yoqib/o'chirganini tekshirib,
    keyin Notification jadvaliga 'pending' holatda yozadi."""
    pref_field = TYPE_TO_PREF_FIELD.get(notification_type)
    if pref_field:
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        if not getattr(prefs, pref_field):
            return None  # foydalanuvchi shu turdagi xabarlarni o'chirib qo'ygan

    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        text=text,
        scheduled_for=scheduled_for,
    )
