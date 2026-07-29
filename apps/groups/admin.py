from django.contrib import admin
from .models import Group, GroupMembership, Announcement


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    Guruhni to'liq Django Admin orqali ham yaratish mumkin: 'owner' maydonida
    kimni egasi qilib tanlasangiz, saqlashda avtomatik ravishda o'sha
    foydalanuvchiga shu guruh doirasida 'Group Owner' roli beriladi —
    xuddi botning o'zi orqali guruh yaratilgandagidek.
    """
    list_display = ("id", "name", "owner", "invite_code", "active_members_count", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "invite_code", "owner__full_name", "owner__username")
    autocomplete_fields = ["owner"]
    inlines = [GroupMembershipInline]
    readonly_fields = ("invite_code",)
    actions = ["activate_groups", "deactivate_groups"]

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new:
            from apps.users.models import Role, UserRole
            role, _ = Role.objects.get_or_create(name=Role.GROUP_OWNER)
            UserRole.objects.get_or_create(user=obj.owner, role=role, group=obj)
            # Owner avtomatik guruhning a'zosi (mentor sifatida) ham qilib qo'yiladi
            GroupMembership.objects.get_or_create(
                user=obj.owner, group=obj, defaults={"role_in_group": GroupMembership.MENTOR}
            )

    @admin.action(description="🟢 Tanlangan guruhlarni faollashtirish")
    def activate_groups(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="🔴 Tanlangan guruhlarni faolsizlantirish")
    def deactivate_groups(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "group", "role_in_group", "is_active")
    list_filter = ("role_in_group", "is_active")
    search_fields = ("user__full_name", "group__name")
    autocomplete_fields = ["user", "group"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """
    E'lonni Django Admin ichidan yaratib, 'Guruh a'zolariga yuborish' action'i
    orqali DARHOL, botning o'zi orqali (Celery talab qilinmaydi) yuborish mumkin —
    bu botdagi '📢 E'lon yozish' funksiyasining Django Admin ekvivalenti.
    """
    list_display = ("id", "group", "author", "is_sent", "created_at")
    list_filter = ("is_sent", "group")
    search_fields = ("text", "group__name")
    autocomplete_fields = ["group", "author"]
    actions = ["send_announcement_now"]

    @admin.action(description="📤 Tanlangan e'lonlarni guruh a'zolariga darhol yuborish")
    def send_announcement_now(self, request, queryset):
        import telebot
        from django.conf import settings
        from django.contrib import messages
        from apps.groups.models import GroupMembership
        from apps.notifications.models import Notification
        from services.notification_service import send_now_bulk

        if not settings.BOT_TOKEN:
            self.message_user(request, "❌ BOT_TOKEN sozlanmagan (.env faylini tekshiring).", level=messages.ERROR)
            return

        bot = telebot.TeleBot(settings.BOT_TOKEN)
        total_sent = 0
        for announcement in queryset.filter(is_sent=False):
            members = [
                m.user for m in GroupMembership.objects.filter(
                    group=announcement.group, is_active=True
                ).exclude(user=announcement.author).select_related("user")
            ]
            result = send_now_bulk(
                bot, members, Notification.ANNOUNCEMENT,
                f"📢 {announcement.group.name}: {announcement.text}",
            )
            total_sent += result["sent"]
            announcement.is_sent = True
            announcement.save(update_fields=["is_sent"])

        self.message_user(request, f"✅ Jami {total_sent} ta a'zoga yuborildi.")
