from django.contrib import admin
from .models import XPTransaction, UserLevel, Badge, UserBadge, Streak


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "reason", "group", "created_at")
    list_filter = ("reason",)
    search_fields = ("user__full_name",)


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "level", "total_xp", "updated_at")
    search_fields = ("user__full_name",)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("id", "icon_emoji", "code", "title")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "badge", "earned_at")
    list_filter = ("badge",)


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "current_daily", "longest_daily", "last_active_date", "freeze_available")
