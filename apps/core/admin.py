from django.contrib import admin
from .models import AdminActionLog, BotSetting


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_telegram_id", "action", "target_model", "target_id")
    list_filter = ("action", "target_model", "created_at")
    search_fields = ("actor_telegram_id", "action", "target_model")
    readonly_fields = [f.name for f in AdminActionLog._meta.fields]

    def has_add_permission(self, request):
        # Loglar faqat tizim tomonidan yaratiladi, qo'lda qo'shib bo'lmaydi.
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BotSetting)
class BotSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description")
    search_fields = ("key",)
