from django.db import models


class Notification(models.Model):
    """
    Har bir bildirishnoma avval shu jadvalga 'pending' holatda yoziladi,
    keyin Celery worker navbat asosida Telegram API orqali yuboradi
    (Telegram flood-control limitlariga rioya qilish uchun MUHIM — to'g'ridan-to'g'ri
    handler ichidan sync yuborilmaydi).
    """
    DEADLINE = "deadline"
    HOMEWORK = "homework"
    INACTIVITY = "inactivity"
    STREAK = "streak"
    REPORT = "report"
    ANNOUNCEMENT = "announcement"
    SYSTEM = "system"
    TYPE_CHOICES = [
        (DEADLINE, "Deadline reminder"), (HOMEWORK, "Homework reminder"),
        (INACTIVITY, "Inactivity reminder"), (STREAK, "Streak reminder"),
        (REPORT, "Productivity report"), (ANNOUNCEMENT, "Announcement"),
        (SYSTEM, "System notification"),
    ]

    PENDING, SENT, FAILED = "pending", "sent", "failed"
    STATUS_CHOICES = [(PENDING, "Pending"), (SENT, "Sent"), (FAILED, "Failed")]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    text = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    scheduled_for = models.DateTimeField(db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "scheduled_for"])]
        ordering = ["scheduled_for"]

    def __str__(self):
        return f"{self.notification_type} -> {self.user} @ {self.scheduled_for}"


class NotificationPreference(models.Model):
    """Foydalanuvchi har bir bildirishnoma turini alohida yoqib/o'chira oladi."""
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="notification_prefs")
    deadline_reminders = models.BooleanField(default=True)
    homework_reminders = models.BooleanField(default=True)
    inactivity_reminders = models.BooleanField(default=True)
    streak_reminders = models.BooleanField(default=True)
    daily_report = models.BooleanField(default=True)
    weekly_report = models.BooleanField(default=True)
    announcements = models.BooleanField(default=True)

    def __str__(self):
        return f"Prefs: {self.user}"
