from django.contrib import admin
from .models import User, Role, UserRole


class UserRoleInline(admin.TabularInline):
    """
    Foydalanuvchi sahifasidan to'g'ridan-to'g'ri rol biriktirish/olib tashlash
    imkonini beradi. `group` maydonini bo'sh qoldirsangiz — global rol
    (masalan Admin, Super Admin) beriladi; guruh tanlasangiz — faqat o'sha
    guruh doirasidagi rol (Mentor, Group Owner) beriladi.
    """
    model = UserRole
    extra = 0
    fk_name = "user"
    autocomplete_fields = ["group"]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "full_name", "username", "telegram_id",
        "role_badges", "is_premium", "is_banned", "can_create_group", "last_active_at",
    )
    list_filter = ("is_premium", "is_banned", "can_create_group", "language")
    search_fields = ("full_name", "username", "telegram_id")
    inlines = [UserRoleInline]
    actions = [
        "ban_users", "unban_users", "grant_premium", "allow_group_creation",
        "make_admin", "make_super_admin", "remove_admin_roles",
    ]

    @admin.display(description="Rollar")
    def role_badges(self, obj):
        names = list(obj.roles.select_related("role").values_list("role__name", flat=True))
        if not names:
            return "—"
        labels = {
            "super_admin": "👑 Super Admin", "admin": "🛠 Admin", "mentor": "🧑‍🏫 Mentor",
            "group_owner": "📚 Owner", "user": "User",
        }
        return ", ".join(labels.get(n, n) for n in set(names))

    @admin.action(description="🚫 Tanlangan foydalanuvchilarni ban qilish")
    def ban_users(self, request, queryset):
        queryset.update(is_banned=True)

    @admin.action(description="✅ Tanlangan foydalanuvchilarni ban'dan chiqarish")
    def unban_users(self, request, queryset):
        queryset.update(is_banned=False)

    @admin.action(description="⭐ Premium berish")
    def grant_premium(self, request, queryset):
        queryset.update(is_premium=True)

    @admin.action(description="👥 Guruh yaratish ruxsatini berish")
    def allow_group_creation(self, request, queryset):
        queryset.update(can_create_group=True)

    @admin.action(description="🛠 Adminlikka tayinlash (global)")
    def make_admin(self, request, queryset):
        """
        SO'RALGAN ASOSIY IMKONIYAT: Django Admin panelida foydalanuvchi(lar)ni
        tanlab, shu action orqali ularni botning global Admin roliga tayinlash mumkin —
        alohida shell buyruqlariga hojat qolmaydi.
        """
        role, _ = Role.objects.get_or_create(name=Role.ADMIN)
        for user in queryset:
            UserRole.objects.get_or_create(user=user, role=role, group=None)
        self.message_user(request, f"{queryset.count()} ta foydalanuvchi Admin qilib tayinlandi.")

    @admin.action(description="👑 Super Adminlikka tayinlash (global, ehtiyot bo'ling)")
    def make_super_admin(self, request, queryset):
        role, _ = Role.objects.get_or_create(name=Role.SUPER_ADMIN)
        for user in queryset:
            UserRole.objects.get_or_create(user=user, role=role, group=None)
        self.message_user(request, f"{queryset.count()} ta foydalanuvchi Super Admin qilib tayinlandi.")

    @admin.action(description="🗑 Global Admin/Super Admin rollarini olib tashlash")
    def remove_admin_roles(self, request, queryset):
        UserRole.objects.filter(
            user__in=queryset, role__name__in=[Role.ADMIN, Role.SUPER_ADMIN], group__isnull=True
        ).delete()
        self.message_user(request, "Tanlangan foydalanuvchilardan global admin rollari olib tashlandi.")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "group")
    list_filter = ("role",)
    search_fields = ("user__full_name", "user__username")
