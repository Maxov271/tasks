"""
Rol tekshiruvi uchun decorator. Har bir admin/mentor/owner-only handler
funksiyasi ustiga qo'yiladi:

    @require_role(Role.ADMIN, Role.SUPER_ADMIN)
    def handle_admin_users(message_or_call, user):
        ...

Guruhga xos rol tekshiruvi uchun (masalan "shu guruhning mentorimi") group_id
parametri beriladi — shunda faqat o'sha guruh doirasidagi rol tekshiriladi.
"""
import functools

from apps.users.models import Role, UserRole


def user_has_role(user, *role_names, group=None) -> bool:
    qs = UserRole.objects.filter(user=user, role__name__in=role_names)
    if group is not None:
        qs = qs.filter(group=group) | qs.filter(group__isnull=True, role__name=Role.SUPER_ADMIN)
    else:
        qs = qs.filter(group__isnull=True)
    return qs.exists()


def require_role(*role_names, group_param: str = None):
    """
    group_param berilsa, wrapped funksiya kwargs'idan shu nomdagi Group obyektini
    olib, faqat o'sha guruh doirasidagi rolni tekshiradi (masalan mentor tekshiruvi).
    """
    def decorator(handler_func):
        @functools.wraps(handler_func)
        def wrapper(update, user, *args, **kwargs):
            group = kwargs.get(group_param) if group_param else None
            if not user_has_role(user, *role_names, group=group):
                # Bot javobi handler darajasida yuboriladi — bu yerda faqat bloklaymiz
                from bot.utils.formatters import PRIORITY_EMOJI  # noqa: F401 (import chegarasi uchun misol)
                raise PermissionError("Bu amal uchun sizda yetarli huquq yo'q.")
            return handler_func(update, user, *args, **kwargs)
        return wrapper
    return decorator
