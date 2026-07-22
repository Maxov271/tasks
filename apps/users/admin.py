from django.contrib import admin
from .models import User, Role, UserRole


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    fk_name = "user"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "username", "telegram_id", "is_premium", "is_banned", "can_create_group", "last_active_at")
    list_filter = ("is_premium", "is_banned", "can_create_group", "language")
    search_fields = ("full_name", "username", "telegram_id")
    inlines = [UserRoleInline]
    actions = ["ban_users", "unban_users", "grant_premium", "allow_group_creation"]

    @admin.action(description="Tanlangan foydalanuvchilarni ban qilish")
    def ban_users(self, request, queryset):
        queryset.update(is_banned=True)

    @admin.action(description="Tanlangan foydalanuvchilarni ban'dan chiqarish")
    def unban_users(self, request, queryset):
        queryset.update(is_banned=False)

    @admin.action(description="Premium berish")
    def grant_premium(self, request, queryset):
        queryset.update(is_premium=True)

    @admin.action(description="Guruh yaratish ruxsatini berish")
    def allow_group_creation(self, request, queryset):
        queryset.update(can_create_group=True)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "group")
    list_filter = ("role",)
    search_fields = ("user__full_name", "user__username")
