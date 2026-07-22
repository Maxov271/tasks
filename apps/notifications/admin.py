from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "notification_type", "status", "scheduled_for", "sent_at")
    list_filter = ("notification_type", "status")
    search_fields = ("user__full_name",)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "deadline_reminders", "homework_reminders", "streak_reminders")
