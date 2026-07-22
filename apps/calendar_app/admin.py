from django.contrib import admin
from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "group", "event_type", "starts_at")
    list_filter = ("event_type",)
    search_fields = ("title", "user__full_name")
