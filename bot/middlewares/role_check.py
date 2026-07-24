"""
Rol tekshiruvi. Ikki xil ehtiyoj bor:

1. `user_has_role(user, *roles)` — MENYU ko'rsatish uchun: "bu userda umuman
   shu rol bormi, qaysi guruhda bo'lishidan qat'iy nazar" (masalan "🛠 Admin
   Panel" tugmasini ko'rsatish/ko'rsatmaslik).
2. `require_role(*roles)` decorator — AMALNI BAJARISHDAN OLDIN qat'iy tekshirish
   uchun (global rollar: Admin/Super Admin har doim global bo'ladi).

Guruhga xos rollar (Mentor/Group Owner) uchun alohida `user_has_group_role()`
funksiyasi ishlatiladi — chunki ular faqat ma'lum bitta guruh doirasida amal qiladi.
"""
import functools

from apps.users.models import Role, UserRole


def user_has_role(user, *role_names) -> bool:
    """Foydalanuvchida shu rollardan biri bor-yo'qligini tekshiradi
    (guruh doirasidan qat'iy nazar — menyu ko'rsatish uchun ishlatiladi)."""
    return UserRole.objects.filter(user=user, role__name__in=role_names).exists()


def user_has_group_role(user, group, *role_names) -> bool:
    """Foydalanuvchi aynan shu guruhda shu rollardan biriga egami.
    Super Admin har qanday guruhda ham avtomatik ruxsatga ega."""
    if UserRole.objects.filter(user=user, role__name=Role.SUPER_ADMIN, group__isnull=True).exists():
        return True
    return UserRole.objects.filter(user=user, role__name__in=role_names, group=group).exists()


def require_role(*role_names):
    """
    Global rollar (Admin, Super Admin) uchun. Handler funksiyalar botda doim
    `(bot, call_or_message, user, ...)` tartibida chaqiriladi — decorator ham
    shu tartibga mos.
    """
    def decorator(handler_func):
        @functools.wraps(handler_func)
        def wrapper(bot, update, user, *args, **kwargs):
            if not user_has_role(user, *role_names):
                raise PermissionError("Bu amal uchun sizda yetarli huquq yo'q.")
            return handler_func(bot, update, user, *args, **kwargs)
        return wrapper
    return decorator


def require_group_role(*role_names):
    """
    Guruhga xos rollar uchun. Wrapped funksiya kwargs orqali `group=` obyektini
    o'zi uzatishi kerak (masalan mentor-only guruh sozlamalari)."""
    def decorator(handler_func):
        @functools.wraps(handler_func)
        def wrapper(bot, update, user, *args, **kwargs):
            group = kwargs.get("group")
            if group is None or not user_has_group_role(user, group, *role_names):
                raise PermissionError("Bu amal uchun sizda yetarli huquq yo'q.")
            return handler_func(bot, update, user, *args, **kwargs)
        return wrapper
    return decorator
