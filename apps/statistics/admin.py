from django.contrib import admin
from .models import StatsSnapshot


@admin.register(StatsSnapshot)
class StatsSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "scope", "scope_id", "period", "generated_at")
    list_filter = ("scope", "period")
    readonly_fields = ("generated_at",)
